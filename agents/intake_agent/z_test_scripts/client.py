import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture(scope="session")
def client():
    """
    Creates a single TestClient for entire test session.
    Lifespan runs only once.
    """
    with TestClient(app) as client:
        yield client
