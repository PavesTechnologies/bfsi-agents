"""Mock USPS Address Verification adapter."""

from .interfaces import USPSAddressInput, USPSAddressResult


class MockUSPSAdapter:
    """Stateless mock USPS address verification adapter.

    No state, no database, no side effects.
    Behavior is deterministic and predictable for testing.
    """

    @staticmethod
    def verify_address(address_input: USPSAddressInput) -> USPSAddressResult:
        """Verify address using mock USPS logic.

        Args:
            address_input: Address data to verify

        Returns:
            USPSAddressResult with verification status and details
        """
        # Empty address line means not deliverable
        if not address_input.address_line1 or not address_input.address_line1.strip():
            return USPSAddressResult(deliverable=False, confidence=0.0)

        # Mock: valid address if address_line1 is provided and not empty
        standardized = (
            f"{address_input.address_line1.strip()}"
            f"{
                ' ' + address_input.address_line2.strip()
                if address_input.address_line2
                else ''
            }"
        )

        return USPSAddressResult(
            deliverable=True,
            standardized_address=standardized,
            zip5=address_input.zip_code[:5] if address_input.zip_code else None,
            zip4="1234",
            confidence=0.9,
        )
