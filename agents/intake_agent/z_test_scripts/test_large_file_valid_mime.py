import pytest

APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

# Only VALID MIME types per document
VALID_MIME_MAP = {
    "drivers-license": ["image/png", "image/jpeg"],
    "ssn-card": ["image/png", "image/jpeg"],
    "passport": ["image/png", "image/jpeg"],
    "w2": ["application/pdf", "image/png", "image/jpeg"],
    "pay-stub": ["application/pdf"],
}


@pytest.mark.parametrize("doc_type,mime_types", VALID_MIME_MAP.items())
def test_large_file_valid_mime_returns_413(client, doc_type, mime_types):
    """
    Upload 20MB file with valid MIME type.
    Expect 413 Payload Too Large.
    """

    large_content = b"x" * (20 * 1024 * 1024)

    for mime in mime_types:
        filename = (
            "large_test.pdf"
            if mime == "application/pdf"
            else "large_test.png"
        )

        response = client.post(
            f"/documents/upload/{doc_type}",
            data={"application_id": APPLICATION_ID},
            files={
                "file": (
                    filename,
                    large_content,
                    mime,
                )
            },
        )

        assert response.status_code == 413