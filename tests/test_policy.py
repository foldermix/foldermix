from __future__ import annotations

import pytest

from foldermix import policy
from foldermix.policy import PolicyEvaluator, normalize_policy_rules


def test_normalize_policy_rules_rejects_rule_without_matchers() -> None:
    with pytest.raises(ValueError) as exc:
        normalize_policy_rules(
            [
                {
                    "rule_id": "R1",
                    "description": "No matchers defined",
                }
            ]
        )

    assert "must define at least one matcher field" in str(exc.value)


def test_normalize_policy_rules_normalizes_extensions() -> None:
    rules = normalize_policy_rules(
        [
            {
                "rule_id": "R1",
                "description": "Only docs",
                "ext_in": ["MD", ".TXT"],
            }
        ]
    )

    assert len(rules) == 1
    assert rules[0].ext_in == (".md", ".txt")


def test_normalize_policy_rules_rejects_bad_regex() -> None:
    with pytest.raises(ValueError) as exc:
        normalize_policy_rules(
            [
                {
                    "rule_id": "R1",
                    "description": "Bad regex",
                    "content_regex": "(",
                }
            ]
        )

    assert "not a valid regex" in str(exc.value)


def test_normalize_policy_rules_rejects_duplicate_rule_ids() -> None:
    with pytest.raises(ValueError) as exc:
        normalize_policy_rules(
            [
                {"rule_id": "dup", "description": "first", "path_glob": "*.txt"},
                {"rule_id": "dup", "description": "second", "path_glob": "*.md"},
            ]
        )

    assert "must be unique" in str(exc.value)


def test_policy_evaluator_is_deterministic_by_rule_id() -> None:
    rules = normalize_policy_rules(
        [
            {
                "rule_id": "rule-b",
                "description": "B",
                "stage": "convert",
                "path_glob": "*.txt",
            },
            {
                "rule_id": "rule-a",
                "description": "A",
                "stage": "convert",
                "path_glob": "*.txt",
            },
        ]
    )
    evaluator = PolicyEvaluator(rules)

    findings = evaluator.evaluate_converted(
        path="note.txt",
        ext=".txt",
        size_bytes=10,
        content="hello",
    )

    assert [finding.rule_id for finding in findings] == ["rule-a", "rule-b"]


def test_policy_evaluator_emits_typed_reason_codes_by_stage() -> None:
    rules = normalize_policy_rules(
        [
            {
                "rule_id": "scan-skip",
                "description": "Flag excluded ext skips",
                "stage": "scan",
                "skip_reason_in": ["excluded_ext"],
                "severity": "low",
                "action": "warn",
            },
            {
                "rule_id": "convert-content",
                "description": "Flag secret markers",
                "stage": "convert",
                "content_regex": "SECRET_[0-9]+",
                "severity": "high",
                "action": "deny",
            },
            {
                "rule_id": "pack-total",
                "description": "Bundle too large",
                "stage": "pack",
                "max_total_bytes": 5,
            },
        ]
    )
    evaluator = PolicyEvaluator(rules)

    scan_findings = evaluator.evaluate_scan_skipped(
        path="image.png",
        skip_reason="excluded_ext",
    )
    convert_findings = evaluator.evaluate_converted(
        path="a.txt",
        ext=".txt",
        size_bytes=12,
        content="SECRET_123",
    )
    pack_findings = evaluator.evaluate_pack_summary(file_count=1, total_bytes=9)

    assert scan_findings[0].reason_code == "POLICY_SKIP_REASON_MATCH"
    assert convert_findings[0].reason_code == "POLICY_CONTENT_REGEX_MATCH"
    assert convert_findings[0].action == "deny"
    assert pack_findings[0].reason_code == "POLICY_TOTAL_BYTES_EXCEEDED"


def test_policy_evaluator_returns_empty_when_path_glob_does_not_match() -> None:
    evaluator = PolicyEvaluator(
        normalize_policy_rules(
            [
                {
                    "rule_id": "glob-only",
                    "description": "glob",
                    "stage": "convert",
                    "path_glob": "*.md",
                }
            ]
        )
    )
    findings = evaluator.evaluate_converted(path="a.txt", ext=".txt", size_bytes=1, content="x")
    assert findings == []


@pytest.mark.parametrize(
    ("rule", "event_kwargs"),
    [
        (
            {
                "rule_id": "ext-mismatch",
                "description": "ext",
                "stage": "convert",
                "ext_in": [".md"],
            },
            {"path": "a.txt", "ext": ".txt", "size_bytes": 1, "content": "x"},
        ),
        (
            {
                "rule_id": "skip-mismatch",
                "description": "skip",
                "stage": "scan",
                "skip_reason_in": ["missing"],
            },
            {"path": "a.txt", "skip_reason": "excluded_ext"},
        ),
        (
            {
                "rule_id": "regex-mismatch",
                "description": "regex",
                "stage": "convert",
                "content_regex": "SECRET_[0-9]+",
            },
            {"path": "a.txt", "ext": ".txt", "size_bytes": 1, "content": "no-secret"},
        ),
        (
            {
                "rule_id": "size-threshold",
                "description": "size",
                "stage": "convert",
                "max_size_bytes": 100,
            },
            {"path": "a.txt", "ext": ".txt", "size_bytes": 10, "content": "x"},
        ),
    ],
)
def test_policy_evaluator_returns_empty_for_non_triggering_matchers(
    rule: dict[str, object], event_kwargs: dict[str, object]
) -> None:
    evaluator = PolicyEvaluator(normalize_policy_rules([rule]))

    if rule.get("stage") == "scan":
        findings = evaluator.evaluate_scan_skipped(**event_kwargs)  # type: ignore[arg-type]
    else:
        findings = evaluator.evaluate_converted(**event_kwargs)  # type: ignore[arg-type]
    assert findings == []


def test_policy_evaluator_pack_threshold_non_triggering_cases_return_empty() -> None:
    evaluator = PolicyEvaluator(
        normalize_policy_rules(
            [
                {
                    "rule_id": "pack-total",
                    "description": "total",
                    "stage": "pack",
                    "max_total_bytes": 100,
                },
                {
                    "rule_id": "pack-count",
                    "description": "count",
                    "stage": "pack",
                    "max_file_count": 5,
                },
            ]
        )
    )

    findings = evaluator.evaluate_pack_summary(file_count=2, total_bytes=20)
    assert findings == []


def test_normalize_policy_rules_validation_errors_cover_type_branches() -> None:
    with pytest.raises(ValueError, match="rule_id"):
        normalize_policy_rules([{"description": "missing id", "path_glob": "*"}])

    with pytest.raises(ValueError, match="path_glob"):
        normalize_policy_rules(
            [{"rule_id": "r", "description": "d", "path_glob": 123}]  # type: ignore[list-item]
        )

    with pytest.raises(ValueError, match="severity must be a string"):
        normalize_policy_rules(
            [{"rule_id": "r", "description": "d", "path_glob": "*", "severity": 1}]  # type: ignore[list-item]
        )

    with pytest.raises(ValueError, match="severity must be one of"):
        normalize_policy_rules(
            [
                {
                    "rule_id": "r",
                    "description": "d",
                    "path_glob": "*",
                    "severity": "urgent",
                }
            ]
        )

    with pytest.raises(ValueError, match="max_size_bytes"):
        normalize_policy_rules(
            [
                {
                    "rule_id": "r",
                    "description": "d",
                    "path_glob": "*",
                    "max_size_bytes": -1,
                }
            ]
        )

    with pytest.raises(ValueError, match="ext_in"):
        normalize_policy_rules(
            [{"rule_id": "r", "description": "d", "path_glob": "*", "ext_in": "txt"}]  # type: ignore[list-item]
        )


def test_normalize_ext_private_helper_none_and_empty() -> None:
    assert policy._normalize_ext(None) is None
    assert policy._normalize_ext("") == ""


def test_policy_evaluator_ext_rule_returns_empty_when_event_has_no_ext() -> None:
    evaluator = PolicyEvaluator(
        normalize_policy_rules(
            [
                {
                    "rule_id": "need-ext",
                    "description": "needs extension",
                    "stage": "any",
                    "ext_in": [".txt"],
                }
            ]
        )
    )

    findings = evaluator.evaluate_scan_skipped(path="a.txt", skip_reason="excluded_ext")
    assert findings == []


def test_policy_evaluator_content_rule_returns_empty_when_event_has_no_content() -> None:
    evaluator = PolicyEvaluator(
        normalize_policy_rules(
            [
                {
                    "rule_id": "need-content",
                    "description": "needs content",
                    "stage": "any",
                    "content_regex": "SECRET_[0-9]+",
                }
            ]
        )
    )

    findings = evaluator.evaluate_scan_included(path="a.txt", ext=".txt", size_bytes=1)
    assert findings == []


def test_policy_evaluator_ext_rule_matches_when_event_ext_is_allowed() -> None:
    evaluator = PolicyEvaluator(
        normalize_policy_rules(
            [
                {
                    "rule_id": "allow-txt",
                    "description": "txt files",
                    "stage": "convert",
                    "ext_in": [".txt"],
                }
            ]
        )
    )

    findings = evaluator.evaluate_converted(path="a.txt", ext=".TXT", size_bytes=1, content="ok")
    assert len(findings) == 1
    assert findings[0].reason_code == "POLICY_RULE_MATCH"


def test_policy_evaluator_pack_file_count_limit_emits_reason_and_message() -> None:
    evaluator = PolicyEvaluator(
        normalize_policy_rules(
            [
                {
                    "rule_id": "pack-count",
                    "description": "Too many files",
                    "stage": "pack",
                    "max_file_count": 1,
                }
            ]
        )
    )

    findings = evaluator.evaluate_pack_summary(file_count=2, total_bytes=1)
    assert len(findings) == 1
    assert findings[0].reason_code == "POLICY_FILE_COUNT_EXCEEDED"
    assert findings[0].message == "Too many files (file_count=2, max_file_count=1)"


def test_normalize_ext_private_helper_normalizes_uppercase_dotted() -> None:
    assert policy._normalize_ext(".TXT") == ".txt"
