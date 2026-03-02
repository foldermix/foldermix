from __future__ import annotations

import fnmatch
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

PolicySeverity = Literal["low", "medium", "high", "critical"]
PolicyAction = Literal["warn", "deny"]
PolicyStage = Literal["scan", "convert", "pack", "any"]
EvaluationStage = Literal["scan", "convert", "pack"]

_VALID_SEVERITIES: set[str] = {"low", "medium", "high", "critical"}
_VALID_ACTIONS: set[str] = {"warn", "deny"}
_VALID_STAGES: set[str] = {"scan", "convert", "pack", "any"}

_MATCHER_FIELDS: set[str] = {
    "path_glob",
    "ext_in",
    "skip_reason_in",
    "content_regex",
    "max_size_bytes",
    "max_total_bytes",
    "max_file_count",
}


@dataclass(frozen=True, slots=True)
class PolicyRule:
    rule_id: str
    description: str
    severity: PolicySeverity = "medium"
    action: PolicyAction = "warn"
    stage: PolicyStage = "any"
    path_glob: str | None = None
    ext_in: tuple[str, ...] | None = None
    skip_reason_in: tuple[str, ...] | None = None
    content_regex: str | None = None
    max_size_bytes: int | None = None
    max_total_bytes: int | None = None
    max_file_count: int | None = None


@dataclass(frozen=True, slots=True)
class PolicyFinding:
    rule_id: str
    severity: PolicySeverity
    action: PolicyAction
    stage: EvaluationStage
    path: str | None
    reason_code: str
    message: str


def normalize_policy_rules(raw_rules: Sequence[Mapping[str, object]]) -> list[PolicyRule]:
    rules: list[PolicyRule] = []
    for idx, raw in enumerate(raw_rules):
        where = f"policy_rules[{idx}]"
        rule_id = _expect_nonempty_string(raw.get("rule_id"), f"{where}.rule_id")
        description = _expect_nonempty_string(raw.get("description"), f"{where}.description")
        severity = _expect_literal(
            raw.get("severity", "medium"), _VALID_SEVERITIES, f"{where}.severity"
        )
        action = _expect_literal(raw.get("action", "warn"), _VALID_ACTIONS, f"{where}.action")
        stage = _expect_literal(raw.get("stage", "any"), _VALID_STAGES, f"{where}.stage")
        path_glob = _expect_optional_string(raw.get("path_glob"), f"{where}.path_glob")
        ext_in = _expect_optional_str_list(raw.get("ext_in"), f"{where}.ext_in", normalize_ext=True)
        skip_reason_in = _expect_optional_str_list(
            raw.get("skip_reason_in"), f"{where}.skip_reason_in"
        )
        content_regex = _expect_optional_string(raw.get("content_regex"), f"{where}.content_regex")
        max_size_bytes = _expect_optional_non_negative_int(
            raw.get("max_size_bytes"), f"{where}.max_size_bytes"
        )
        max_total_bytes = _expect_optional_non_negative_int(
            raw.get("max_total_bytes"), f"{where}.max_total_bytes"
        )
        max_file_count = _expect_optional_non_negative_int(
            raw.get("max_file_count"), f"{where}.max_file_count"
        )

        if content_regex is not None:
            try:
                re.compile(content_regex)
            except re.error as exc:
                raise ValueError(f"{where}.content_regex is not a valid regex: {exc}") from exc

        has_matcher = any(
            field in raw and raw[field] is not None  # type: ignore[index]
            for field in _MATCHER_FIELDS
        )
        if not has_matcher:
            raise ValueError(
                f"{where} must define at least one matcher field: "
                + ", ".join(sorted(_MATCHER_FIELDS))
            )

        rules.append(
            PolicyRule(
                rule_id=rule_id,
                description=description,
                severity=severity,  # type: ignore[arg-type]
                action=action,  # type: ignore[arg-type]
                stage=stage,  # type: ignore[arg-type]
                path_glob=path_glob,
                ext_in=ext_in,
                skip_reason_in=skip_reason_in,
                content_regex=content_regex,
                max_size_bytes=max_size_bytes,
                max_total_bytes=max_total_bytes,
                max_file_count=max_file_count,
            )
        )

    return rules


@dataclass(slots=True)
class _Event:
    stage: EvaluationStage
    path: str | None = None
    ext: str | None = None
    size_bytes: int | None = None
    skip_reason: str | None = None
    content: str | None = None
    total_bytes: int | None = None
    file_count: int | None = None


class PolicyEvaluator:
    def __init__(self, rules: Sequence[PolicyRule]) -> None:
        self._rules = sorted(
            rules,
            key=lambda rule: (rule.stage, rule.rule_id.casefold()),
        )
        self._compiled_regex: dict[str, re.Pattern[str]] = {}
        for rule in self._rules:
            if rule.content_regex is not None:
                self._compiled_regex[rule.rule_id] = re.compile(rule.content_regex)

    def evaluate_scan_included(
        self, *, path: str, ext: str, size_bytes: int
    ) -> list[PolicyFinding]:
        return self._evaluate(
            _Event(stage="scan", path=path, ext=ext, size_bytes=size_bytes),
        )

    def evaluate_scan_skipped(self, *, path: str, skip_reason: str) -> list[PolicyFinding]:
        return self._evaluate(
            _Event(stage="scan", path=path, skip_reason=skip_reason),
        )

    def evaluate_converted(
        self, *, path: str, ext: str, size_bytes: int, content: str
    ) -> list[PolicyFinding]:
        return self._evaluate(
            _Event(stage="convert", path=path, ext=ext, size_bytes=size_bytes, content=content),
        )

    def evaluate_pack_summary(self, *, file_count: int, total_bytes: int) -> list[PolicyFinding]:
        return self._evaluate(
            _Event(stage="pack", file_count=file_count, total_bytes=total_bytes),
        )

    def _evaluate(self, event: _Event) -> list[PolicyFinding]:
        findings: list[PolicyFinding] = []
        for rule in self._rules:
            if not _rule_applies_to_stage(rule, event.stage):
                continue

            reason_code = self._matches(rule, event)
            if reason_code is None:
                continue

            findings.append(
                PolicyFinding(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    action=rule.action,
                    stage=event.stage,
                    path=event.path,
                    reason_code=reason_code,
                    message=_build_finding_message(rule, event, reason_code),
                )
            )
        return findings

    def _matches(self, rule: PolicyRule, event: _Event) -> str | None:
        matched_content_regex = False
        matched_skip_reason = False
        matched_size_limit = False
        matched_total_limit = False
        matched_count_limit = False

        if rule.path_glob is not None:
            if event.path is None or not fnmatch.fnmatch(event.path, rule.path_glob):
                return None
        if rule.ext_in is not None:
            normalized_ext = _normalize_ext(event.ext) if event.ext is not None else None
            if normalized_ext is None or normalized_ext not in rule.ext_in:
                return None
        if rule.skip_reason_in is not None:
            if event.skip_reason is None or event.skip_reason not in rule.skip_reason_in:
                return None
            matched_skip_reason = True
        if rule.content_regex is not None:
            if event.content is None:
                return None
            pattern = self._compiled_regex[rule.rule_id]
            if pattern.search(event.content) is None:
                return None
            matched_content_regex = True
        if rule.max_size_bytes is not None:
            if event.size_bytes is None or event.size_bytes <= rule.max_size_bytes:
                return None
            matched_size_limit = True
        if rule.max_total_bytes is not None:
            if event.total_bytes is None or event.total_bytes <= rule.max_total_bytes:
                return None
            matched_total_limit = True
        if rule.max_file_count is not None:
            if event.file_count is None or event.file_count <= rule.max_file_count:
                return None
            matched_count_limit = True

        if matched_total_limit:
            return "POLICY_TOTAL_BYTES_EXCEEDED"
        if matched_count_limit:
            return "POLICY_FILE_COUNT_EXCEEDED"
        if matched_size_limit:
            return "POLICY_FILE_SIZE_EXCEEDED"
        if matched_content_regex:
            return "POLICY_CONTENT_REGEX_MATCH"
        if matched_skip_reason:
            return "POLICY_SKIP_REASON_MATCH"
        return "POLICY_RULE_MATCH"


def _rule_applies_to_stage(rule: PolicyRule, stage: EvaluationStage) -> bool:
    return rule.stage == "any" or rule.stage == stage


def _build_finding_message(rule: PolicyRule, event: _Event, reason_code: str) -> str:
    if reason_code == "POLICY_FILE_SIZE_EXCEEDED" and event.size_bytes is not None:
        return f"{rule.description} (size={event.size_bytes}, max_size_bytes={rule.max_size_bytes})"
    if reason_code == "POLICY_TOTAL_BYTES_EXCEEDED" and event.total_bytes is not None:
        return (
            f"{rule.description} (total_bytes={event.total_bytes}, "
            f"max_total_bytes={rule.max_total_bytes})"
        )
    if reason_code == "POLICY_FILE_COUNT_EXCEEDED" and event.file_count is not None:
        return (
            f"{rule.description} (file_count={event.file_count}, "
            f"max_file_count={rule.max_file_count})"
        )
    if reason_code == "POLICY_SKIP_REASON_MATCH" and event.skip_reason is not None:
        return f"{rule.description} (skip_reason={event.skip_reason})"
    return rule.description


def _normalize_ext(ext: str | None) -> str | None:
    if ext is None:
        return None
    if ext == "":
        return ""
    return ext if ext.startswith(".") else f".{ext}".lower()


def _expect_nonempty_string(value: object, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where} must be a non-empty string")
    return value


def _expect_optional_string(value: object, where: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{where} must be a string")
    return value


def _expect_literal(value: object, choices: set[str], where: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{where} must be a string")
    if value not in choices:
        raise ValueError(f"{where} must be one of: {', '.join(sorted(choices))}")
    return value


def _expect_optional_non_negative_int(value: object, where: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{where} must be a non-negative integer")
    return value


def _expect_optional_str_list(
    value: object, where: str, *, normalize_ext: bool = False
) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{where} must be a list of strings")
    if normalize_ext:
        normalized = tuple(_normalize_ext(item.lower()) or "" for item in value)
        return normalized
    return tuple(value)
