class MissingRuleError(RuntimeError):
    """Raised when a rule key required by an analyzer is absent or inactive
    in the bank-admin DB. The Indian flow halts so the bank fixes the gap
    before applications run with stale code-defaults."""

    def __init__(self, rule_key: str, category: str):
        self.rule_key = rule_key
        self.category = category
        super().__init__(
            f"Required rule '{rule_key}' missing or inactive in category '{category}' (bank-admin DB)."
        )
