import pytest

# Valid UUID for testing
APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

DOCUMENT_TYPES = [
    "drivers-license",
    "ssn-card",
    "passport",
    "w2",
    "pay-stub"
]

FILE_VARIANTS = [
    ("large_image.png", "image/png"),
    ("large_image.jpg", "image/jpeg"),
    ("large_document.pdf", "application/pdf"),
    ("large_text.txt", "text/plain"),
]


@pytest.mark.parametrize("doc_type", DOCUMENT_TYPES)
@pytest.mark.parametrize("filename,content_type", FILE_VARIANTS)
def test_large_file_upload(client, doc_type, filename, content_type):
    """
    Upload 20MB file to each document type.
    Expect 413 Payload Too Large.
    """

    large_content = b"x" * (20 * 1024 * 1024)

    response = client.post(
        f"/documents/upload/{doc_type}",
        data={"application_id": APPLICATION_ID},
        files={
            "file": (
                filename,
                large_content,
                content_type,
            )
        },
    )

    assert response.status_code == 413
