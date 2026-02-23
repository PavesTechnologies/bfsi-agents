"""
Tests for Evidence Linking

Test cases:
- Evidence linked correctly into canonical output
- Deterministic ordering across runs
- Duplicate evidence removed
- Missing evidence handled gracefully
- Canonical output unchanged except evidence section
- Traceability fields preserved
- Unicode/long paths handled safely
"""

from copy import deepcopy
import pytest

from src.domain.output.canonical_builder import assemble_canonical_output
from src.domain.output.evidence import (
    EvidenceReference,
    link_evidence_to_output,
    deduplicate_evidence,
    sort_evidence,
    get_evidence_by_type,
    get_evidence_by_entity,
)


class TestEvidenceImmutability:
    """Test that EvidenceReference is immutable."""

    def test_evidence_reference_is_frozen(self):
        """EvidenceReference should be immutable."""
        evidence = EvidenceReference(
            id="EV-001",
            type="validation",
            source="validator_1",
            path="/docs/id.jpg",
            created_at="2026-02-10T10:30:00Z",
        )

        # Attempting to mutate should raise FrozenInstanceError
        with pytest.raises(AttributeError):
            evidence.id = "EV-002"

    def test_evidence_reference_with_optional_fields(self):
        """EvidenceReference should support optional traceability fields."""
        evidence = EvidenceReference(
            id="EV-001",
            type="validation",
            source="email_validator",
            path="/validations/email.json",
            created_at="2026-02-10T10:30:00Z",
            entity_type="applicant",
            entity_id="APPL-001",
            rule_id="EMAIL_FORMAT",
        )

        assert evidence.entity_type == "applicant"
        assert evidence.entity_id == "APPL-001"
        assert evidence.rule_id == "EMAIL_FORMAT"

    def test_evidence_reference_to_dict(self):
        """EvidenceReference should convert to dict."""
        evidence = EvidenceReference(
            id="EV-001",
            type="validation",
            source="validator_1",
            path="/docs/id.jpg",
            created_at="2026-02-10T10:30:00Z",
            entity_type="applicant",
            entity_id="APPL-001",
        )

        evidence_dict = evidence.to_dict()

        assert evidence_dict["id"] == "EV-001"
        assert evidence_dict["type"] == "validation"
        assert evidence_dict["source"] == "validator_1"
        assert evidence_dict["path"] == "/docs/id.jpg"
        assert evidence_dict["entity_type"] == "applicant"
        assert evidence_dict["entity_id"] == "APPL-001"


class TestEvidenceLinking:
    """Test evidence linking into canonical output."""

    def test_evidence_linked_into_output(self):
        """Evidence should be linked into canonical output."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="ssn_validator",
                path="/validations/ssn.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-002",
                type="document",
                source="document_scanner",
                path="/documents/id.jpg",
                created_at="2026-02-10T10:30:01Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        # Check evidence section
        assert "evidence" in output
        assert len(output["evidence"]) == 2
        assert any(e["id"] == "EV-001" for e in output["evidence"])
        assert any(e["id"] == "EV-002" for e in output["evidence"])

    def test_evidence_with_traceability_fields_preserved(self):
        """Traceability fields should be preserved in output."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="email_validator",
                path="/validations/email.json",
                created_at="2026-02-10T10:30:00Z",
                entity_type="applicant",
                entity_id="APPL-001",
                rule_id="EMAIL_FORMAT",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        evidence_item = output["evidence"][0]
        assert evidence_item["entity_type"] == "applicant"
        assert evidence_item["entity_id"] == "APPL-001"
        assert evidence_item["rule_id"] == "EMAIL_FORMAT"

    def test_evidence_linked_with_existing_evidence_in_output(self):
        """New evidence should merge with existing evidence."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[
                {"path": "/existing/path1.pdf", "type": "EXISTING"}
            ],
            generated_at="2026-02-10T10:30:00Z",
        )

        new_evidence = [
            EvidenceReference(
                id="EV-002",
                type="validation",
                source="validator",
                path="/new/path2.pdf",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=new_evidence,
        )

        # Both old and new evidence should be present
        paths = [e["path"] for e in output["evidence"]]
        assert "/existing/path1.pdf" in paths
        assert "/new/path2.pdf" in paths

    def test_none_values_filtered_from_evidence_dict(self):
        """Evidence dicts should not include None values."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="validator",
                path="/path.json",
                created_at="2026-02-10T10:30:00Z",
                # entity_type and others are None
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        evidence_item = output["evidence"][0]
        # None values should be filtered out
        assert "entity_type" not in evidence_item
        assert "entity_id" not in evidence_item
        assert "rule_id" not in evidence_item


class TestEvidenceOrdering:
    """Test deterministic evidence ordering."""

    def test_evidence_sorted_by_type_source_id(self):
        """Evidence should be sorted deterministically."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-003",
                type="validation",
                source="zzz_validator",
                path="/z.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="aaa_validator",
                path="/a.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-002",
                type="enrichment",
                source="mmm_service",
                path="/m.json",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        # Should be sorted by path (which is the final sort)
        paths = [e["path"] for e in output["evidence"]]
        assert paths == sorted(paths)

    def test_evidence_ordering_stable_across_calls(self):
        """Same evidence should produce identical ordering across calls."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id=f"EV-{i:03d}",
                type="validation" if i % 2 == 0 else "enrichment",
                source=f"source_{i}",
                path=f"/path_{i}.json",
                created_at="2026-02-10T10:30:00Z",
            )
            for i in range(10, 0, -1)  # Reverse order
        ]

        output1 = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )
        output2 = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        # Evidence should be in same order
        assert output1["evidence"] == output2["evidence"]


class TestDuplicateRemoval:
    """Test duplicate evidence removal."""

    def test_duplicate_evidence_removed_by_id(self):
        """Duplicate evidence (by id) should be removed."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="validator_1",
                path="/path1.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-001",  # Duplicate ID
                type="validation",
                source="validator_2",
                path="/path2.json",
                created_at="2026-02-10T10:30:01Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        # Should only have one evidence item (first one seen)
        assert len(output["evidence"]) == 1
        assert output["evidence"][0]["id"] == "EV-001"
        assert output["evidence"][0]["source"] == "validator_1"

    def test_many_duplicates_handled(self):
        """Many duplicate evidence items should be deduplicated."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Create 100 evidence items, 50 unique
        evidence = []
        for i in range(100):
            evidence.append(
                EvidenceReference(
                    id=f"EV-{i % 50:03d}",  # Only 50 unique IDs
                    type="validation",
                    source=f"source_{i}",
                    path=f"/path_{i}.json",
                    created_at="2026-02-10T10:30:00Z",
                )
            )

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        # Should have exactly 50 unique items
        assert len(output["evidence"]) == 50
        ids = [e["id"] for e in output["evidence"]]
        assert len(ids) == len(set(ids))  # All unique


class TestInputImmutability:
    """Test that inputs are not mutated."""

    def test_canonical_output_not_mutated(self):
        """Canonical output should not be mutated."""
        original_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )
        output_copy = deepcopy(original_output)

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="validator",
                path="/path.json",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        link_evidence_to_output(
            canonical_output=original_output,
            evidence_refs=evidence,
        )

        # Original should not be changed
        assert original_output == output_copy

    def test_evidence_refs_not_mutated(self):
        """Evidence references should not be mutated."""
        evidence_original = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="validator",
                path="/path.json",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]
        evidence_copy = deepcopy(evidence_original)

        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence_original,
        )

        # Original should not be changed
        assert evidence_original == evidence_copy


class TestEmptyEvidence:
    """Test handling of empty evidence."""

    def test_empty_evidence_list(self):
        """Empty evidence list should be handled gracefully."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=[],
        )

        # Evidence section should exist and be empty
        assert "evidence" in output
        assert output["evidence"] == []

    def test_no_evidence_provided_preserves_existing(self):
        """Not providing evidence should preserve existing evidence."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[
                {"path": "/existing.pdf", "type": "EXISTING"}
            ],
            generated_at="2026-02-10T10:30:00Z",
        )

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=[],
        )

        # Existing evidence should still be there
        assert len(output["evidence"]) == 1
        assert output["evidence"][0]["path"] == "/existing.pdf"


class TestHelperFunctions:
    """Test helper functions."""

    def test_deduplicate_evidence(self):
        """Deduplicate function should remove duplicates by id."""
        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="v1",
                path="/p1.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="v2",
                path="/p2.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-002",
                type="validation",
                source="v3",
                path="/p3.json",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        unique = deduplicate_evidence(evidence)

        assert len(unique) == 2
        assert unique[0].id == "EV-001"
        assert unique[1].id == "EV-002"

    def test_sort_evidence(self):
        """Sort function should order evidence deterministically."""
        evidence = [
            EvidenceReference(
                id="EV-003",
                type="validation",
                source="zz",
                path="/path.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-001",
                type="enrichment",
                source="aa",
                path="/path.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-002",
                type="validation",
                source="aa",
                path="/path.json",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        sorted_evidence = sort_evidence(evidence)

        # Should be sorted: enrichment < validation, then by source, then by id
        assert sorted_evidence[0].type == "enrichment"
        assert sorted_evidence[1].type == "validation"
        assert sorted_evidence[1].id == "EV-002"
        assert sorted_evidence[2].id == "EV-003"

    def test_get_evidence_by_type(self):
        """Filter evidence by type."""
        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="v1",
                path="/p1.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-002",
                type="enrichment",
                source="e1",
                path="/p2.json",
                created_at="2026-02-10T10:30:00Z",
            ),
            EvidenceReference(
                id="EV-003",
                type="validation",
                source="v2",
                path="/p3.json",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        validations = get_evidence_by_type(evidence, "validation")

        assert len(validations) == 2
        assert all(e.type == "validation" for e in validations)

    def test_get_evidence_by_entity(self):
        """Filter evidence by entity type and id."""
        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="v1",
                path="/p1.json",
                created_at="2026-02-10T10:30:00Z",
                entity_type="applicant",
                entity_id="APPL-001",
            ),
            EvidenceReference(
                id="EV-002",
                type="validation",
                source="v2",
                path="/p2.json",
                created_at="2026-02-10T10:30:00Z",
                entity_type="applicant",
                entity_id="APPL-002",
            ),
            EvidenceReference(
                id="EV-003",
                type="validation",
                source="v3",
                path="/p3.json",
                created_at="2026-02-10T10:30:00Z",
                entity_type="address",
                entity_id="ADDR-001",
            ),
        ]

        appl_001_evidence = get_evidence_by_entity(evidence, "applicant", "APPL-001")

        assert len(appl_001_evidence) == 1
        assert appl_001_evidence[0].entity_id == "APPL-001"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_paths(self):
        """Unicode characters in paths should be handled safely."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="document",
                source="scanner",
                path="/documents/José_García_请求.pdf",
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        assert output["evidence"][0]["path"] == "/documents/José_García_请求.pdf"

    def test_very_long_paths(self):
        """Very long paths should be handled safely."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        long_path = "/documents/" + "x" * 10000 + ".pdf"

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="document",
                source="scanner",
                path=long_path,
                created_at="2026-02-10T10:30:00Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        assert output["evidence"][0]["path"] == long_path

    def test_complex_evidence_mix(self):
        """Complex mix of evidence types and sources should be handled."""
        canonical_output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                {
                    "applicant_id": "APPL-002",
                    "applicant_role": "CO-APPLICANT",
                    "first_name": "Jane",
                    "last_name": "Doe",
                },
            ],
            enrichments={
                "credit": {"score": 750},
            },
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        evidence = [
            EvidenceReference(
                id="EV-001",
                type="validation",
                source="email_validator",
                path="/validations/email_appl1.json",
                created_at="2026-02-10T10:30:00Z",
                entity_type="applicant",
                entity_id="APPL-001",
            ),
            EvidenceReference(
                id="EV-002",
                type="validation",
                source="phone_validator",
                path="/validations/phone_appl2.json",
                created_at="2026-02-10T10:30:01Z",
                entity_type="applicant",
                entity_id="APPL-002",
            ),
            EvidenceReference(
                id="EV-003",
                type="enrichment",
                source="credit_bureau",
                path="/enrichments/credit_appl1.json",
                created_at="2026-02-10T10:30:02Z",
                entity_type="applicant",
                entity_id="APPL-001",
                rule_id="CREDIT_CHECK",
            ),
            EvidenceReference(
                id="EV-004",
                type="document",
                source="document_store",
                path="/documents/id_appl1.jpg",
                created_at="2026-02-10T10:30:03Z",
            ),
        ]

        output = link_evidence_to_output(
            canonical_output=canonical_output,
            evidence_refs=evidence,
        )

        # All evidence should be present and properly linked
        assert len(output["evidence"]) == 4
        appl1_evidence = [
            e for e in output["evidence"] if e.get("entity_id") == "APPL-001"
        ]
        assert len(appl1_evidence) == 2
