import json
from datetime import datetime
from fastapi.testclient import TestClient
from src.main import app

OUTPUT_FILE = "z_test_scripts/large_file_test_output.json"


def store_response(data):
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(data, indent=4))
        f.write("\n\n")


def test_upload_large_files_all_types():
    application_id = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

    document_types = [
        "drivers-license",
        "ssn-card",
        "passport",
        "w2",
        "pay-stub"
    ]

    # File variations (20MB each)
    file_variants = [
        {
            "filename": "large_image.png",
            "content": b"x" * (20 * 1024 * 1024),
            "content_type": "image/png"
        },
        {
            "filename": "large_image.jpg",
            "content": b"x" * (20 * 1024 * 1024),
            "content_type": "image/jpeg"
        },
        {
            "filename": "large_document.pdf",
            "content": b"x" * (20 * 1024 * 1024),
            "content_type": "application/pdf"
        },
        {
            "filename": "large_text.txt",
            "content": b"x" * (20 * 1024 * 1024),
            "content_type": "text/plain"
        },
    ]

    with TestClient(app) as client:

        for doc_type in document_types:
            for file_data in file_variants:

                response = client.post(
                    f"/documents/upload/{doc_type}",
                    data={"application_id": application_id},
                    files={
                        "file": (
                            file_data["filename"],
                            file_data["content"],
                            file_data["content_type"],
                        )
                    },
                )

                result = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "endpoint": f"/documents/upload/{doc_type}",
                    "file_name": file_data["filename"],
                    "content_type": file_data["content_type"],
                    "status_code": response.status_code,
                    "application_id": application_id,
                    "response": response.json() if response.content else {}
                }

                store_response(result)

                print(
                    f"{doc_type} | {file_data['filename']} "
                    f"-> {response.status_code}"
                )


# Execute once
test_upload_large_files_all_types()
