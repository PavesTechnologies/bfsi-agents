import pytest
import io
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.mark.asyncio
async def test_document_upload_idempotent(tmp_path):
    # Use bytes directly or wrap in BytesIO; httpx is flexible
    file_content = b"fake-pdf-content"
    
    # In httpx, the files format is slightly different: (name, (filename, content, content_type))
    files = {
        "file": ("test.pdf", file_content, "application/pdf")
    }
    data = {
        "application_id": "cccccccc-cccc-cccc-cccc-cccccccccccc"
    }

    # ASGITransport bridges the client directly to your FastAPI app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as ac:
        # First Request
        r1 = await ac.post("/documents/upload/w2", data=data, files=files)
        assert r1.status_code == 200

        # Second Request (Checking idempotency)
        # Note: If your endpoint consumes the file stream, 
        # you might need to recreate the 'files' dict for the second call
        r2 = await ac.post("/documents/upload/w2", data=data, files=files)
        assert r2.status_code == 200

        # Assertions
        assert r1.json()["document_id"] == r2.json()["document_id"]