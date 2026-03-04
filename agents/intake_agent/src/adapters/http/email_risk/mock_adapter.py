"""Mock Email Domain Risk adapter."""
from .interfaces import EmailInput, EmailRiskResult


class MockEmailAdapter:
    """Stateless mock email domain risk adapter.
    
    No state, no database, no side effects.
    Deterministic mock behavior for testing.
    """

    # Low risk domains
    _LOW_RISK_DOMAINS = {"gmail.com", "outlook.com", "yahoo.com", "icloud.com"}
    
    # High risk disposable domains
    _DISPOSABLE_DOMAINS = {"mailinator.com", "tempmail.com", "guerrillamail.com"}

    @staticmethod
    def analyze_email_domain(email_input: EmailInput) -> EmailRiskResult:
        """Analyze email domain risk using mock logic.
        
        Mock behavior:
        - gmail.com, outlook.com → low risk
        - mailinator, tempmail, guerrillamail → high risk, disposable
        - others → medium risk
        
        Args:
            email_input: Email address to analyze
            
        Returns:
            EmailRiskResult with domain risk assessment
        """
        if not email_input.email or "@" not in email_input.email:
            return EmailRiskResult(
                domain="",
                risk="high",
                disposable=True,
                confidence=0.0
            )

        # Extract domain
        try:
            domain = email_input.email.split("@")[1].lower().strip()
        except IndexError:
            return EmailRiskResult(
                domain="",
                risk="high",
                disposable=True,
                confidence=0.0
            )

        # Check if disposable
        is_disposable = domain in MockEmailAdapter._DISPOSABLE_DOMAINS

        # Determine risk level
        if domain in MockEmailAdapter._LOW_RISK_DOMAINS:
            risk = "low"
            confidence = 0.95
        elif is_disposable:
            risk = "high"
            confidence = 0.98
        else:
            risk = "medium"
            confidence = 0.80

        return EmailRiskResult(
            domain=domain,
            risk=risk,
            disposable=is_disposable,
            confidence=confidence
        )
