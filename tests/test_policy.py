from __future__ import annotations

import pytest

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
