import boto3
import os
import re
from PIL import Image
from botocore.exceptions import ClientError
from datetime import datetime
import uuid


# ================= CONFIG =================

BUCKET_NAME = "ajay-ocr-bucket-12345"
REGION = "us-east-1"

# =========================================


class AWSOCR:

    def __init__(self):

        self.s3 = boto3.client("s3", region_name=REGION)
        self.textract = boto3.client("textract", region_name=REGION)

    # ---------------------------------------
    # Convert image to supported JPG
    # ---------------------------------------
    def normalize_image(self, file_path):

        try:
            # 1. Validate extension
            ext = os.path.splitext(file_path)[1].lower()

            if ext not in [".jpg", ".jpeg", ".png"]:
                print("[ERROR] Unsupported file type:", ext)
                raise ValueError("Unsupported file type")
                
            img = Image.open(file_path)
            img = img.convert("RGB")

            # Random local filename
            temp_name = f"temp_{uuid.uuid4().hex}.jpg"

            img.save(
                temp_name,
                format="JPEG",
                quality=95,
                progressive=False,
                optimize=True
            )

            print("[INFO] Normalized image:", temp_name)

            return temp_name

        except Exception as e:

            print("[ERROR] Image normalization failed:", e)
            return None

    # ---------------------------------------
    # Upload to S3
    # ---------------------------------------
    def upload_to_s3(self, local_path, s3_filename):
        try:

            self.s3.upload_file(
                local_path,
                BUCKET_NAME,
                s3_filename
            )

            print("[INFO] Uploaded to S3 as:", s3_filename)

            return s3_filename

        except Exception as e:

            print("[ERROR] Upload failed:", e)
            return None

    # ---------------------------------------
    # Delete from S3
    # ---------------------------------------
    def delete_from_s3(self, filename):

        try:

            self.s3.delete_object(
                Bucket=BUCKET_NAME,
                Key=filename
            )
            print("[INFO] Deleted from S3:", filename)
        except Exception as e:
            print("[ERROR] Delete failed:", e)

    # ---------------------------------------
    # OCR
    # ---------------------------------------
    def extract_text(self, filename):

        try:

            response = self.textract.detect_document_text(
                Document={
                    "S3Object": {
                        "Bucket": BUCKET_NAME,
                        "Name": filename
                    }
                }
            )

            lines = []

            for block in response["Blocks"]:
                if block["BlockType"] == "LINE":
                    lines.append(block["Text"].upper())

            return lines

        except ClientError as e:
            print("[ERROR] Textract failed:", e)
            return None

    # ---------------------------------------
    # Main Pipeline
    # ---------------------------------------

    def process_file(self, user_file, document_type, application_id):

        print("\n[START] Processing:", user_file)

        # ----------------------------
        # Step 1: Normalize
        # ----------------------------

        temp_file = self.normalize_image(user_file)

        if not temp_file:
            return {"status": "failed", "reason": "image_processing_failed"}

        # ----------------------------
        # Step 2: Build S3 Name
        # ----------------------------

        s3_filename = f"{document_type}_{application_id}.jpg"

        # ----------------------------
        # Step 3: Upload
        # ----------------------------

        filename = self.upload_to_s3(temp_file, s3_filename)

        if not filename:
            os.remove(temp_file)
            return {"status": "failed", "reason": "upload_failed"}

        # ----------------------------
        # Step 4: OCR
        # ----------------------------

        lines = self.extract_text(filename)
        print("[INFO] OCR Extracted Lines:", lines)
        
        if not lines:

            self.delete_from_s3(filename)
            os.remove(temp_file)
            return {"status": "failed", "reason": "ocr_failed"}

        # ----------------------------
        try:
            os.remove(temp_file)
            print("[INFO] Temp file deleted")
        except:
            pass

        # ----------------------------
        # Success
        # ----------------------------

        return {
            "status": "success",
            "s3_file": filename,
            "lines": lines
        }