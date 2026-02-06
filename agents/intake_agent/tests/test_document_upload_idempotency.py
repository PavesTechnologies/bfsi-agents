import io
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_document_upload_idempotent(tmp_path):
    file_content = b"fake-pdf-content"
    files = {
        "file": ("test.pdf", io.BytesIO(file_content), "application/pdf")
    }
    data = {
        "application_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"
    }

    r1 = client.post("/documents/upload/w2", data=data, files=files)
    assert r1.status_code == 200

    r2 = client.post("/documents/upload/w2", data=data, files=files)
    assert r2.status_code == 200

    assert r1.json()["document_id"] == r2.json()["document_id"]
