import json
from datetime import datetime
from fastapi.testclient import TestClient
from src.main import app

OUTPUT_FILE = r"z_test_scripts\dl_upload_test_output.txt"

def store_response(data):
    with open(OUTPUT_FILE, "a") as f:
        f.write(json.dumps(data, indent=4))
        f.write("\n\n")


def test_upload_ssn_card():
    application_id = "a41b53c5-1975-4dcb-9307-c2c514138b2f"

    # Path to a sample file in your project
    # file_path = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\ssn2.jpg" test 1
    # file_path = r"C:\Users\Ajaykumar.Bhukya\Downloads\ssn\barcode_working.jpg" test 2
    file_path = r"C:\Users\Ajaykumar.Bhukya\Downloads\Sri_Charan_credentials.csv"

    with TestClient(app) as client:
        with open(file_path, "rb") as f:
            response = client.post(
                "/documents/upload/drivers-license",
                data={"application_id": application_id},
                files={"file": ("sample_dl.jpg", f, "image/jpeg")},
            )

        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "endpoint": "/documents/upload/drivers-license",
            "status_code": response.status_code,
            "file_name": file_path,
            "application_id": application_id,
            "response": response.json() if response.content else {}
        }

        store_response(result)

        print("Test case executed. Response stored in:", OUTPUT_FILE)
        
test_upload_ssn_card()