"""
Tests for the final output demo endpoint.

Verifies the complete output pipeline is working:
- Canonical assembly
- LOS schema validation
- Evidence linking
- Callback decision simulation
"""

import pytest
from uuid import uuid4

from fastapi.testclient import TestClient
from src.app import create_app


# Create test client
app = create_app()
client = TestClient(app)


@pytest.mark.asyncio
async def test_finalize_demo_success():
    """Test success flow: valid output, success callback simulated."""
    app_id = uuid4()
    
    response = client.post(
        "/loan_intake/finalize_application_demo",
        json={
            "application_id": str(app_id),
            "simulate_partial": False,
            "simulate_failure": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "SUCCESS"
    assert data["schema_valid"] is True
    assert data["callback_simulated"] == "SUCCESS_CALLBACK"
    assert data["evidence_count"] == 3
    assert data["canonical_output"] is not None
    assert "application_id" in data["canonical_output"]


@pytest.mark.asyncio
async def test_finalize_demo_partial():
    """Test partial success flow: valid output with warnings."""
    app_id = uuid4()
    
    response = client.post(
        "/loan_intake/finalize_application_demo",
        json={
            "application_id": str(app_id),
            "simulate_partial": True,
            "simulate_failure": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "PARTIAL_SUCCESS"
    assert data["schema_valid"] is True
    assert data["callback_simulated"] == "PARTIAL_SUCCESS_CALLBACK"
    assert data["evidence_count"] == 3


@pytest.mark.asyncio
async def test_finalize_demo_failure():
    """Test failure flow: schema validation fails, failure callback simulated."""
    app_id = uuid4()
    
    response = client.post(
        "/loan_intake/finalize_application_demo",
        json={
            "application_id": str(app_id),
            "simulate_partial": False,
            "simulate_failure": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "FAILURE"
    assert data["schema_valid"] is False
    assert data["callback_simulated"] == "FAILURE_CALLBACK"
    assert data["canonical_output"] is None
    assert data["error_reason"] is not None
