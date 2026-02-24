"""Enrichment service - orchestrates adapter calls."""

from src.adapters.http.email_risk import EmailInput, MockEmailAdapter
from src.adapters.http.employer import EmployerInput, MockEmployerAdapter
from src.adapters.http.phone import MockPhoneAdapter, PhoneInput
from src.adapters.http.usps import MockUSPSAdapter, USPSAddressInput
from src.api.v1.schemas.enrichment import (
    EmailRequestSchema,
    EmailResponseSchema,
    EmployerRequestSchema,
    EmployerResponseSchema,
    PhoneRequestSchema,
    PhoneResponseSchema,
    USPSAddressRequestSchema,
    USPSAddressResponseSchema,
)


class EnrichmentService:
    """Service layer for enrichment operations.

    Orchestrates calls to mock adapters. No database access, no side effects.
    """

    @staticmethod
    def verify_address(
        request: USPSAddressRequestSchema,
    ) -> USPSAddressResponseSchema:
        """Verify address using USPS mock adapter.

        Args:
            request: Address verification request

        Returns:
            Address verification response with deliverability and ZIP+4
        """
        adapter_input = USPSAddressInput(
            address_line1=request.address_line1,
            address_line2=request.address_line2,
            city=request.city,
            state=request.state,
            zip_code=request.zip_code,
        )

        adapter_result = MockUSPSAdapter.verify_address(adapter_input)

        return USPSAddressResponseSchema(
            deliverable=adapter_result.deliverable,
            standardized_address=adapter_result.standardized_address,
            zip5=adapter_result.zip5,
            zip4=adapter_result.zip4,
            confidence=adapter_result.confidence,
        )

    @staticmethod
    def verify_employer(
        request: EmployerRequestSchema,
    ) -> EmployerResponseSchema:
        """Verify employer using mock adapter.

        Args:
            request: Employer verification request

        Returns:
            Employer verification response with NAICS code
        """
        adapter_input = EmployerInput(
            employer_name=request.employer_name,
            state=request.state,
            naics_code=request.naics_code,
        )

        adapter_result = MockEmployerAdapter.verify_employer(adapter_input)

        return EmployerResponseSchema(
            verified=adapter_result.verified,
            naics_code=adapter_result.naics_code,
            confidence=adapter_result.confidence,
        )

    @staticmethod
    def analyze_phone(
        request: PhoneRequestSchema,
    ) -> PhoneResponseSchema:
        """Analyze phone using mock adapter.

        Args:
            request: Phone analysis request

        Returns:
            Phone intelligence response with validity and line type
        """
        adapter_input = PhoneInput(phone_number=request.phone_number)

        adapter_result = MockPhoneAdapter.analyze_phone(adapter_input)

        return PhoneResponseSchema(
            valid=adapter_result.valid,
            line_type=adapter_result.line_type,
            carrier=adapter_result.carrier,
            confidence=adapter_result.confidence,
        )

    @staticmethod
    def analyze_email_domain(
        request: EmailRequestSchema,
    ) -> EmailResponseSchema:
        """Analyze email domain using mock adapter.

        Args:
            request: Email analysis request

        Returns:
            Email risk response with domain risk classification
        """
        adapter_input = EmailInput(email=request.email)

        adapter_result = MockEmailAdapter.analyze_email_domain(adapter_input)

        return EmailResponseSchema(
            domain=adapter_result.domain,
            risk=adapter_result.risk,
            disposable=adapter_result.disposable,
            confidence=adapter_result.confidence,
        )
