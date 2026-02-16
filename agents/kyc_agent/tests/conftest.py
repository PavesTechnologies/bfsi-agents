# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from src.app import create_app
from src.utils.migration_database import SessionLocal
from src.models.kyc_cases import KYC
from src.models.risk_decision import RiskDecision


@pytest.fixture(scope="function")
def client():
    app = create_app()
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_database():
    db = SessionLocal()
    db.query(RiskDecision).delete()
    db.query(KYC).delete()
    db.commit()
    db.close()
