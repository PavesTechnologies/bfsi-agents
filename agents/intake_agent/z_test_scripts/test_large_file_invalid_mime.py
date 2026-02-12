import pytest

APPLICATION_ID = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

DOCUMENT_TYPES = [
    "drivers-license",
    "ssn-card",
    "passport",
    "w2",
    "pay-stub"
]

# Invalid MIME types for all
INVALID_MIME_TYPES = [
    "text/plain",
    "application/json",
    "application/xml",
]


@pytest.mark.parametrize("doc_type", DOCUMENT_TYPES)
@pytest.mark.parametrize("invalid_mime", INVALID_MIME_TYPES)
def test_invalid_mime_returns_415(client, doc_type, invalid_mime):
    """
    Upload file with invalid MIME type.
    Expect 415 Unsupported Media Type.
    """

    large_content = b"x" * (1 * 1024 * 1024)  # 1MB small file

    response = client.post(
        f"/documents/upload/{doc_type}",
        data={"application_id": APPLICATION_ID},
        files={
            "file": (
                "invalid_file.txt",
                large_content,
                invalid_mime,
            )
        },
    )

    assert response.status_code == 415
