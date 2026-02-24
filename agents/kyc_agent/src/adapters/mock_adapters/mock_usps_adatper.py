from typing import Dict, Any


class MockUSPSAdapter:
    """
    Mock for USPS Address Validation.
    Retrieves standardized data including address type (Residential, Commercial, PO Box)
    and deliverability status.
    """

    def get_address_details(self, address_data: Dict[str, str]) -> Dict[str, Any]:
        # Cleanup and extraction (Section 5.1)
        line1 = address_data.get("line1", "").strip().upper()
        city = address_data.get("city", "").strip().upper()
        state = address_data.get("state", "").strip().upper()
        zip_input = address_data.get("zip", "").strip()

        # Scenario: Address not found / Not Deliverable
        if "GHOST" in line1 or "9999" in zip_input:
            return {
                "status": "INVALID_ADDRESS",
                "error_code": "USPS-001",
                "message": "Address not found in national directory.",
                "deliverable": False,
            }

        # Scenario: Commercial Address (e.g., Office/Business)
        if "OFFICE" in line1 or "SUITE" in line1:
            return {
                "status": "VALIDATED",
                "standardized_address": {
                    "line1": line1,
                    "city": city,
                    "state": state,
                    "zip5": zip_input[:5],
                    "zip4": "5000",
                },
                "delivery_point_validation": "Y",
                "vacant": False,
                "address_type": "Commercial",
                "deliverable": True,
            }

        # Scenario: PO Box Detection (Section 10.1)
        if "PO BOX" in line1:
            return {
                "status": "VALIDATED",
                "standardized_address": {
                    "line1": line1,
                    "city": city,
                    "state": state,
                    "zip5": zip_input[:5],
                    "zip4": "9999",
                },
                "delivery_point_validation": "Y",
                "vacant": False,
                "address_type": "PO Box",
                "deliverable": True,
            }

        # Scenario: Vacant Residential Property (Section 10.1)
        if "VACANT" in line1:
            return {
                "status": "VALIDATED",
                "standardized_address": {
                    "line1": line1,
                    "city": city,
                    "state": state,
                    "zip5": zip_input[:5],
                    "zip4": "0001",
                },
                "delivery_point_validation": "Y",
                "vacant": True,
                "address_type": "Residential",
                "deliverable": True,
            }

        # Default: Successful Residential Standardization (Golden Path)
        return {
            "status": "VALIDATED",
            "standardized_address": {
                "line1": line1,
                "city": city,
                "state": state,
                "zip5": zip_input[:5] if len(zip_input) >= 5 else "12345",
                "zip4": "0001",
            },
            "delivery_point_validation": "Y",
            "vacant": False,
            "address_type": "Residential",
            "deliverable": True,
        }
