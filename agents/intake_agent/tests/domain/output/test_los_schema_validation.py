"""
Tests for LOS Schema Validation

Test cases:
- Valid canonical output passes
- Missing required fields fail
- Wrong data types fail
- Extra/unknown fields fail
- Invalid nested structures fail
- Error messages are deterministic
"""

from copy import deepcopy
import pytest

from src.domain.output.canonical_builder import assemble_canonical_output
from src.domain.output.schema_validator import (
    validate_los_output,
    LOSSchemaValidationError,
)


class TestValidOutput:
    """Test that valid canonical output passes validation."""

    def test_minimal_valid_output(self):
        """Minimal but complete valid output should pass."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
            },
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_complete_valid_output(self):
        """Complete valid output with all optional fields should pass."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "credit_type": "UNSECURED",
                "loan_purpose": "DEBT_CONSOLIDATION",
                "requested_amount": 50000.00,
                "requested_term_months": 60,
                "preferred_payment_day": 15,
                "origination_channel": "ONLINE",
                "application_status": "SUBMITTED",
            },
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "middle_name": "Michael",
                    "last_name": "Doe",
                    "suffix": "Jr.",
                    "date_of_birth": "1985-05-15",
                    "ssn_last4": "1234",
                    "itin_number": None,
                    "citizenship_status": "US_CITIZEN",
                    "email": "john@example.com",
                    "phone_number": "555-0100",
                    "gender": "MALE",
                },
                {
                    "applicant_id": "APPL-002",
                    "applicant_role": "CO-APPLICANT",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "email": "jane@example.com",
                },
            ],
            enrichments={
                "credit_score": {"primary": 750, "co_applicant": 700},
                "employment_verification": {"status": "VERIFIED"},
            },
            evidence_refs=[
                {"path": "/docs/id.jpg", "type": "ID"},
                {"path": "/docs/income.pdf", "type": "PROOF_OF_INCOME"},
            ],
            generated_at="2026-02-10T14:23:45.123456Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_multiple_applicants_valid(self):
        """Multiple applicants in proper order should pass."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {"applicant_id": "APPL-001", "applicant_role": "PRIMARY", "first_name": "Alice", "last_name": "A"},
                {"applicant_id": "APPL-002", "applicant_role": "CO-APPLICANT", "first_name": "Bob", "last_name": "B"},
                {"applicant_id": "APPL-003", "applicant_role": "GUARANTOR", "first_name": "Charlie", "last_name": "C"},
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)


class TestMissingRequiredFields:
    """Test that missing required fields cause validation to fail."""

    def test_missing_application(self):
        """Missing application field should fail."""
        output = {
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "application" in str(exc_info.value).lower()

    def test_missing_applicants(self):
        """Missing applicants field should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "applicants" in str(exc_info.value).lower()

    def test_missing_enrichments(self):
        """Missing enrichments field should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "enrichments" in str(exc_info.value).lower()

    def test_missing_evidence(self):
        """Missing evidence field should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "enrichments": {},
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "evidence" in str(exc_info.value).lower()

    def test_missing_generated_at(self):
        """Missing generated_at field should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "enrichments": {},
            "evidence": [],
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "generated_at" in str(exc_info.value).lower()

    def test_missing_application_id(self):
        """Missing required field in application should fail."""
        output = assemble_canonical_output(
            application={"loan_type": "PERSONAL"},  # Missing application_id
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "application_id" in str(exc_info.value).lower()

    def test_missing_loan_type(self):
        """Missing required field in application should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001"},  # Missing loan_type
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "loan_type" in str(exc_info.value).lower()

    def test_missing_applicant_id(self):
        """Missing required field in applicant should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_role": "PRIMARY",  # Missing applicant_id
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "applicant_id" in str(exc_info.value).lower()

    def test_missing_applicant_role(self):
        """Missing required field in applicant should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",  # Missing applicant_role
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "applicant_role" in str(exc_info.value).lower()

    def test_missing_applicant_first_name(self):
        """Missing required field in applicant should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    # Missing first_name
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "first_name" in str(exc_info.value).lower()

    def test_missing_applicant_last_name(self):
        """Missing required field in applicant should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    # Missing last_name
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "last_name" in str(exc_info.value).lower()

    def test_missing_evidence_path(self):
        """Missing required field in evidence should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[{"type": "ID"}],  # Missing path
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "path" in str(exc_info.value).lower()

    def test_missing_evidence_type(self):
        """Missing required field in evidence should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[{"path": "/docs/id.jpg"}],  # Missing type
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        assert "type" in str(exc_info.value).lower()


class TestWrongDataTypes:
    """Test that wrong data types cause validation to fail."""

    def test_application_not_dict(self):
        """Application field with wrong type should fail."""
        output = {
            "application": "not a dict",  # Should be dict
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_applicants_not_list(self):
        """Applicants field with wrong type should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": "not a list",  # Should be list
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_enrichments_not_dict(self):
        """Enrichments field with wrong type should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "enrichments": [1, 2, 3],  # Should be dict
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_evidence_not_list(self):
        """Evidence field with wrong type should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "enrichments": {},
            "evidence": {"type": "dict"},  # Should be list
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_generated_at_not_string(self):
        """generated_at with wrong type should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": 123456,  # Should be string
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_requested_amount_not_numeric(self):
        """Numeric field with wrong type should fail."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "requested_amount": "not a number",  # Should be float
            },
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_requested_term_months_not_int(self):
        """Int field with wrong type should fail."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "requested_term_months": "not an int",  # Should be int
            },
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_applicant_list_contains_non_dict(self):
        """Applicants list with non-dict items should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                },
                "not a dict",  # Should be dict
            ],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)


class TestExtraFields:
    """Test that unknown/extra fields are rejected."""

    def test_extra_field_in_root(self):
        """Extra field at root level should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )
        output["extra_field"] = "should not be here"

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_extra_field_in_application(self):
        """Extra field in application should fail."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "unknown_field": "should not be here",
            },
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_extra_field_in_applicant(self):
        """Extra field in applicant should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                    "unknown_field": "should not be here",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_extra_field_in_evidence(self):
        """Extra field in evidence should fail."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[
                {
                    "path": "/docs/id.jpg",
                    "type": "ID",
                    "unknown_field": "should not be here",
                }
            ],
            generated_at="2026-02-10T10:30:00Z",
        )

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)


class TestInvalidNestedStructures:
    """Test that invalid nested structures are rejected."""

    def test_applicant_invalid_nested_structure(self):
        """Invalid nested applicant structure should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": 123,  # Should be string
                    "last_name": "Doe",
                }
            ],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_evidence_invalid_nested_structure(self):
        """Invalid nested evidence structure should fail."""
        output = {
            "application": {"application_id": "APP-001", "loan_type": "PERSONAL"},
            "applicants": [],
            "enrichments": {},
            "evidence": [
                {
                    "path": 123,  # Should be string
                    "type": "ID",
                }
            ],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError):
            validate_los_output(output)

    def test_deeply_nested_invalid_type(self):
        """Deeply nested invalid type should fail."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "requested_amount": None,  # OK - optional
            },
            applicants=[],
            enrichments={"custom": {"nested": {"data": "value"}}},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Enrichments can be complex dicts - this should pass
        validate_los_output(output)


class TestErrorMessages:
    """Test that error messages are deterministic and clear."""

    def test_error_includes_field_names(self):
        """Error message should include invalid field names."""
        output = {
            "application": {"application_id": "APP-001"},  # Missing loan_type
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        error = exc_info.value
        assert error.invalid_fields  # Should have list of invalid fields
        assert "application" in error.invalid_fields

    def test_error_has_clear_message(self):
        """Error message should be clear and actionable."""
        output = {
            "application": "not a dict",
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        error = exc_info.value
        assert "schema validation failed" in error.message.lower()
        assert len(error.validation_errors) > 0

    def test_error_deterministic_with_same_invalid_input(self):
        """Same invalid input should produce identical error messages."""
        output = {
            "application": {"loan_type": "PERSONAL"},  # Missing application_id
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        error1 = None
        error2 = None

        try:
            validate_los_output(output)
        except LOSSchemaValidationError as e:
            error1 = str(e)

        try:
            validate_los_output(output)
        except LOSSchemaValidationError as e:
            error2 = str(e)

        # Error messages should be identical for same invalid input
        assert error1 == error2

    def test_error_str_representation(self):
        """Error should have proper string representation."""
        output = {
            "application": "invalid",
            "applicants": [],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        with pytest.raises(LOSSchemaValidationError) as exc_info:
            validate_los_output(output)

        error_str = str(exc_info.value)
        assert error_str  # Should have meaningful string representation
        assert "LOS schema validation failed" in error_str


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_applicants_list_valid(self):
        """Empty applicants list should be valid."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_empty_evidence_list_valid(self):
        """Empty evidence list should be valid."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_empty_enrichments_dict_valid(self):
        """Empty enrichments dict should be valid."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_all_optional_fields_none(self):
        """All optional fields omitted or None should still pass."""
        output = {
            "application": {
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "credit_type": None,
                "loan_purpose": None,
                "requested_amount": None,
            },
            "applicants": [
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": None,
                }
            ],
            "enrichments": {},
            "evidence": [],
            "generated_at": "2026-02-10T10:30:00Z",
        }

        # Should not raise
        validate_los_output(output)

    def test_unicode_in_fields(self):
        """Unicode characters in string fields should be valid."""
        output = assemble_canonical_output(
            application={"application_id": "APP-001", "loan_type": "PERSONAL"},
            applicants=[
                {
                    "applicant_id": "APPL-001",
                    "applicant_role": "PRIMARY",
                    "first_name": "José",
                    "last_name": "García",
                }
            ],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_very_long_strings(self):
        """Very long string values should be valid."""
        long_string = "x" * 10000

        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "loan_purpose": long_string,
            },
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)

    def test_numeric_boundary_values(self):
        """Boundary numeric values should be valid."""
        output = assemble_canonical_output(
            application={
                "application_id": "APP-001",
                "loan_type": "PERSONAL",
                "requested_amount": 0.0,  # Zero
                "requested_term_months": 1,  # Minimum
            },
            applicants=[],
            enrichments={},
            evidence_refs=[],
            generated_at="2026-02-10T10:30:00Z",
        )

        # Should not raise
        validate_los_output(output)
