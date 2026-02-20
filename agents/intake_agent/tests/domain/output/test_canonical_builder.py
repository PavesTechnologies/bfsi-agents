"""
Tests for Canonical Output Builder

Test cases:
- Same input → identical output (determinism)
- Stable ordering of applicants and evidence
- Safe handling of missing enrichments
- No mutation of inputs
- Sorted dictionary keys
"""

import json
from copy import deepcopy

import pytest

from src.domain.output.canonical_builder import assemble_canonical_output


class TestDeterminism:
    """Test that same input always produces identical output."""

    def test_same_input_produces_identical_output(self):
        """Same input should produce byte-for-byte identical output."""
        input_data = {
            "application": {
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "requested_amount": 50000,
            },
            "applicants": [
                {
                    "applicant_id": "APPL-001",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            "enrichments": {"credit_score": {"score": 750}},
            "evidence_refs": [
                {"path": "/documents/id.jpg", "type": "ID"},
                {"path": "/documents/proof.pdf", "type": "PROOF_OF_INCOME"},
            ],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        # Call function multiple times
        output1 = assemble_canonical_output(**input_data)
        output2 = assemble_canonical_output(**input_data)
        output3 = assemble_canonical_output(**input_data)

        # JSON serialization should be identical
        json1 = json.dumps(output1, sort_keys=True)
        json2 = json.dumps(output2, sort_keys=True)
        json3 = json.dumps(output3, sort_keys=True)

        assert json1 == json2
        assert json2 == json3
        assert output1 == output2 == output3

    def test_determinism_with_unordered_input(self):
        """Unordered input dicts should still produce identical output."""
        # Create two identical structures but with keys in different order
        app_a = {"z_field": 1, "a_field": 2, "m_field": 3}
        app_b = {"a_field": 2, "m_field": 3, "z_field": 1}

        output_a = assemble_canonical_output(
            application=app_a, generated_at="2026-02-10T10:30:00Z"
        )
        output_b = assemble_canonical_output(
            application=app_b, generated_at="2026-02-10T10:30:00Z"
        )

        # Both should produce identical output despite input key order
        assert output_a == output_b
        assert (
            json.dumps(output_a, sort_keys=True)
            == json.dumps(output_b, sort_keys=True)
        )


class TestApplicantOrdering:
    """Test that applicants are sorted stably."""

    def test_applicants_sorted_by_applicant_id(self):
        """Applicants should be sorted by applicant_id."""
        applicants = [
            {"applicant_id": "APPL-003", "first_name": "Charlie"},
            {"applicant_id": "APPL-001", "first_name": "Alice"},
            {"applicant_id": "APPL-002", "first_name": "Bob"},
        ]

        output = assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Check ordering
        assert output["applicants"][0]["applicant_id"] == "APPL-001"
        assert output["applicants"][1]["applicant_id"] == "APPL-002"
        assert output["applicants"][2]["applicant_id"] == "APPL-003"

    def test_applicants_sorted_by_role_when_no_id(self):
        """Applicants without IDs should fall back to role sorting."""
        applicants = [
            {"applicant_role": "CO-APPLICANT", "first_name": "Bob"},
            {"applicant_role": "PRIMARY", "first_name": "Alice"},
            {"applicant_role": "GUARANTOR", "first_name": "Charlie"},
        ]

        output = assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Check ordering by role
        assert output["applicants"][0]["applicant_role"] == "CO-APPLICANT"
        assert output["applicants"][1]["applicant_role"] == "GUARANTOR"
        assert output["applicants"][2]["applicant_role"] == "PRIMARY"

    def test_applicants_stable_ordering(self):
        """Applicants should maintain stable ordering across calls."""
        applicants = [
            {
                "applicant_id": "APPL-C",
                "first_name": "Charlie",
                "nested": {"z": 1, "a": 2},
            },
            {
                "applicant_id": "APPL-A",
                "first_name": "Alice",
                "nested": {"y": 3, "b": 4},
            },
            {
                "applicant_id": "APPL-B",
                "first_name": "Bob",
                "nested": {"x": 5, "c": 6},
            },
        ]

        output1 = assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )
        output2 = assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Ordering should be identical across calls
        assert output1["applicants"] == output2["applicants"]
        assert (
            output1["applicants"][0]["applicant_id"]
            == output2["applicants"][0]["applicant_id"]
        )


class TestEvidenceOrdering:
    """Test that evidence is sorted stably by path."""

    def test_evidence_sorted_by_path(self):
        """Evidence should be sorted by path."""
        evidence = [
            {"path": "/documents/proof_of_income.pdf", "type": "INCOME"},
            {"path": "/documents/id_card.jpg", "type": "ID"},
            {"path": "/documents/bank_statement.pdf", "type": "BANK"},
        ]

        output = assemble_canonical_output(
            evidence_refs=evidence,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Check ordering by path
        assert output["evidence"][0]["path"] == "/documents/bank_statement.pdf"
        assert output["evidence"][1]["path"] == "/documents/id_card.jpg"
        assert output["evidence"][2]["path"] == "/documents/proof_of_income.pdf"

    def test_evidence_stable_ordering(self):
        """Evidence should maintain stable ordering across calls."""
        evidence = [
            {"path": "/z_file.pdf", "type": "TYPE_Z"},
            {"path": "/a_file.pdf", "type": "TYPE_A"},
            {"path": "/m_file.pdf", "type": "TYPE_M"},
        ]

        output1 = assemble_canonical_output(
            evidence_refs=evidence,
            generated_at="2026-02-10T10:30:00Z",
        )
        output2 = assemble_canonical_output(
            evidence_refs=evidence,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output1["evidence"] == output2["evidence"]


class TestMissingOptionalSections:
    """Test safe handling of missing optional sections."""

    def test_missing_application(self):
        """Missing application should not break output."""
        output = assemble_canonical_output(
            generated_at="2026-02-10T10:30:00Z",
        )

        assert "application" in output
        assert output["application"] == {}

    def test_missing_applicants(self):
        """Missing applicants should return empty list."""
        output = assemble_canonical_output(
            generated_at="2026-02-10T10:30:00Z",
        )

        assert "applicants" in output
        assert output["applicants"] == []

    def test_missing_enrichments(self):
        """Missing enrichments should not break output."""
        output = assemble_canonical_output(
            generated_at="2026-02-10T10:30:00Z",
        )

        assert "enrichments" in output
        assert output["enrichments"] == {}

    def test_missing_evidence(self):
        """Missing evidence should return empty list."""
        output = assemble_canonical_output(
            generated_at="2026-02-10T10:30:00Z",
        )

        assert "evidence" in output
        assert output["evidence"] == []

    def test_all_missing_sections(self):
        """All missing sections should result in minimal output."""
        output = assemble_canonical_output(
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output == {
            "applicants": [],
            "application": {},
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }


class TestNoMutation:
    """Test that inputs are not mutated."""

    def test_application_not_mutated(self):
        """Application input should not be mutated."""
        application = {"application_id": "APP-001", "status": "SUBMITTED"}
        original = deepcopy(application)

        assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert application == original

    def test_applicants_not_mutated(self):
        """Applicants input should not be mutated."""
        applicants = [
            {"applicant_id": "APPL-002", "first_name": "Bob"},
            {"applicant_id": "APPL-001", "first_name": "Alice"},
        ]
        original = deepcopy(applicants)

        assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert applicants == original

    def test_enrichments_not_mutated(self):
        """Enrichments input should not be mutated."""
        enrichments = {
            "z_field": {"score": 750},
            "a_field": {"status": "approved"},
        }
        original = deepcopy(enrichments)

        assemble_canonical_output(
            enrichments=enrichments,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert enrichments == original

    def test_evidence_not_mutated(self):
        """Evidence input should not be mutated."""
        evidence = [
            {"path": "/z_file.pdf", "type": "TYPE_Z"},
            {"path": "/a_file.pdf", "type": "TYPE_A"},
        ]
        original = deepcopy(evidence)

        assemble_canonical_output(
            evidence_refs=evidence,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert evidence == original


class TestDictionarySorting:
    """Test that all dictionary keys are sorted."""

    def test_top_level_keys_sorted(self):
        """Top-level keys should be sorted."""
        output = assemble_canonical_output(
            generated_at="2026-02-10T10:30:00Z",
        )

        keys = list(output.keys())
        assert keys == sorted(keys)

    def test_nested_dict_keys_sorted(self):
        """Nested dictionary keys should be sorted."""
        application = {
            "z_field": "value_z",
            "a_field": "value_a",
            "m_field": "value_m",
        }

        output = assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        app_keys = list(output["application"].keys())
        assert app_keys == sorted(app_keys)

    def test_deeply_nested_keys_sorted(self):
        """Deeply nested dictionary keys should be sorted."""
        enrichments = {
            "credit_data": {
                "z_score": 750,
                "a_history": "good",
                "m_status": "active",
            }
        }

        output = assemble_canonical_output(
            enrichments=enrichments,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Check nested keys
        credit_keys = list(output["enrichments"]["credit_data"].keys())
        assert credit_keys == sorted(credit_keys)


class TestComplexScenario:
    """Test realistic complex scenarios."""

    def test_full_loan_application_output(self):
        """Test assembly of complete loan application output."""
        application = {
            "application_id": "APP-001",
            "loan_type": "PERSONAL",
            "requested_amount": 50000,
            "status": "SUBMITTED",
        }

        applicants = [
            {
                "applicant_id": "APPL-002",
                "applicant_role": "CO-APPLICANT",
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
            },
            {
                "applicant_id": "APPL-001",
                "applicant_role": "PRIMARY",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
            },
        ]

        enrichments = {
            "credit_score": {"primary": 750, "co_applicant": 700},
            "employment_verification": {"primary": "VERIFIED"},
        }

        evidence = [
            {"path": "/docs/ssn_card.pdf", "type": "ID"},
            {"path": "/docs/payslip.pdf", "type": "INCOME"},
        ]

        output = assemble_canonical_output(
            application=application,
            applicants=applicants,
            enrichments=enrichments,
            evidence_refs=evidence,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Verify structure
        assert output["application"]["application_id"] == "APP-001"
        assert len(output["applicants"]) == 2
        assert output["applicants"][0]["applicant_id"] == "APPL-001"  # Sorted
        assert output["applicants"][1]["applicant_id"] == "APPL-002"
        assert output["evidence"][0]["path"] == "/docs/payslip.pdf"  # Sorted

    def test_output_preserves_all_data(self):
        """Output should preserve all input data."""
        application = {"application_id": "APP-001", "custom_field": "value"}
        applicants = [
            {
                "applicant_id": "APPL-001",
                "custom_nested": {"deep_field": "deep_value"},
            }
        ]
        enrichments = {"custom_enrichment": {"data": [1, 2, 3]}}
        evidence = [{"path": "/file.pdf", "custom_evidence": "custom_value"}]

        output = assemble_canonical_output(
            application=application,
            applicants=applicants,
            enrichments=enrichments,
            evidence_refs=evidence,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Verify data is preserved
        assert output["application"]["custom_field"] == "value"
        assert (
            output["applicants"][0]["custom_nested"]["deep_field"]
            == "deep_value"
        )
        assert output["enrichments"]["custom_enrichment"]["data"] == [1, 2, 3]
        assert output["evidence"][0]["custom_evidence"] == "custom_value"

    def test_generated_at_passed_through_unchanged(self):
        """generated_at should be passed through without modification."""
        generated_at = "2026-02-10T14:23:45.123456Z"

        output = assemble_canonical_output(
            generated_at=generated_at,
        )

        assert output["generated_at"] == generated_at

    def test_empty_collections_not_null(self):
        """Empty collections should be lists/dicts, not None."""
        output = assemble_canonical_output(
            applicants=[],
            evidence_refs=[],
            enrichments={},
            application={},
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output["applicants"] == []
        assert output["evidence"] == []
        assert output["enrichments"] == {}
        assert output["application"] == {}
        assert isinstance(output["applicants"], list)
        assert isinstance(output["evidence"], list)
        assert isinstance(output["enrichments"], dict)
        assert isinstance(output["application"], dict)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_single_applicant(self):
        """Single applicant should be ordered correctly."""
        applicants = [{"applicant_id": "APPL-001", "first_name": "John"}]

        output = assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert len(output["applicants"]) == 1
        assert output["applicants"][0]["applicant_id"] == "APPL-001"

    def test_many_applicants_ordering(self):
        """Many applicants should maintain stable ordering."""
        applicants = [
            {"applicant_id": f"APPL-{i:03d}", "name": f"Person{i}"}
            for i in range(10, 0, -1)  # 10, 9, 8, ...1
        ]

        output = assemble_canonical_output(
            applicants=applicants,
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should be sorted: 1, 2, 3, ... 10
        for i, applicant in enumerate(output["applicants"], start=1):
            assert applicant["applicant_id"] == f"APPL-{i:03d}"

    def test_unicode_in_data(self):
        """Unicode characters should be preserved."""
        application = {
            "applicant_name": "José García",
            "notes": "Special chars: 中文 العربية",
        }

        output = assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output["application"]["applicant_name"] == "José García"
        assert "中文 العربية" in output["application"]["notes"]

    def test_numeric_values_preserved(self):
        """Numeric values should be preserved as-is."""
        application = {
            "integer_field": 12345,
            "float_field": 123.45,
            "zero": 0,
            "negative": -999,
        }

        output = assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output["application"]["integer_field"] == 12345
        assert output["application"]["float_field"] == 123.45
        assert output["application"]["zero"] == 0
        assert output["application"]["negative"] == -999

    def test_boolean_values_preserved(self):
        """Boolean values should be preserved."""
        application = {"is_approved": True, "has_issues": False}

        output = assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output["application"]["is_approved"] is True
        assert output["application"]["has_issues"] is False

    def test_null_values_in_nested_structures(self):
        """None/null values in nested structures should be preserved."""
        application = {
            "field_with_null": None,
            "nested": {"inner_null": None, "inner_value": "value"},
        }

        output = assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert output["application"]["field_with_null"] is None
        assert output["application"]["nested"]["inner_null"] is None
        assert output["application"]["nested"]["inner_value"] == "value"

    def test_lists_in_nested_structures(self):
        """Lists in nested structures should be preserved."""
        application = {
            "addresses": [
                {"street": "123 Main", "city": "NYC"},
                {"street": "456 Oak", "city": "LA"},
            ]
        }

        output = assemble_canonical_output(
            application=application,
            generated_at="2026-02-10T10:30:00Z",
        )

        assert len(output["application"]["addresses"]) == 2
        assert output["application"]["addresses"][0]["street"] == "123 Main"
        # Note: Lists preserve order, not sorted
