"""Mock Employer Verification adapter."""
from .interfaces import EmployerInput, EmployerVerificationResult


class MockEmployerAdapter:
    """Stateless mock employer verification adapter.
    
    No state, no database, no side effects.
    Deterministic mock behavior for testing.
    """

    # Corporate entity keywords
    _CORPORATE_KEYWORDS = {"inc", "corp", "llc", "ltd", "gmbh", "sa", "ag"}

    @staticmethod
    def verify_employer(employer_input: EmployerInput) -> EmployerVerificationResult:
        """Verify employer using mock logic.
        
        Mock behavior:
        - verified=True if employer_name contains corporate keywords (case-insensitive)
        - assigned NAICS "541512" if verified
        
        Args:
            employer_input: Employer data to verify
            
        Returns:
            EmployerVerificationResult with verification status
        """
        if not employer_input.employer_name:
            return EmployerVerificationResult(
                verified=False,
                confidence=0.0
            )

        # Normalize and check for corporate keywords
        normalized = employer_input.employer_name.strip().lower()
        is_verified = any(
            keyword in normalized
            for keyword in MockEmployerAdapter._CORPORATE_KEYWORDS
        )

        return EmployerVerificationResult(
            verified=is_verified,
            normalized_name=employer_input.employer_name.strip(),
            naics_code="541512" if is_verified else None,
            confidence=0.85 if is_verified else 0.0
        )
