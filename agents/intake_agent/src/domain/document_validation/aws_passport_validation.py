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


class PassportOCR:

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
    # Detect if Passport
    # ---------------------------------------
    def is_passport_document(self, lines):

        text = " ".join(lines)

        keywords = [
            "PASSPORT",
            "UNITED STATES OF AMERICA",
            "USA"
        ]

        for k in keywords:
            if k in text:
                return True

        return False
        # ---------------------------------------
    # Confidence Scoring (MRZ-first)
    # ---------------------------------------
    def calculate_confidence(self, lines, mrz_data):

        # 1️⃣ Strongest signal: MRZ success
        if mrz_data:
            base_score = 0.9

            # Small reinforcement from OCR keywords
            if self.is_passport_document(lines):
                base_score += 0.05

            return round(min(base_score, 1.0), 3)

        # 2️⃣ No MRZ → fallback logic (weak)
        score = 0.0

        if self.is_passport_document(lines):
            score += 0.5

        passport_no = self.extract_passport_number(lines)
        if passport_no:
            score += 0.3

        return round(min(score, 0.7), 3)

    # ---------------------------------------
    # Find Passport Number
    # ---------------------------------------
    def extract_passport_number(self, lines):

        text = " ".join(lines)

        patterns = [
        r"\b[A-Z0-9]{9}\b",                 # generic
        r"\bUSA\s*[A-Z0-9]{8,9}\b",          # USA-prefixed
        r"\b[A-Z]\d{8}\b",                   # Passport card format
        ]

        for p in patterns:

            match = re.search(p, text)

            if match:
                return match.group()

        return None

    # ---------------------------------------
    # MRZ Checksum
    # ---------------------------------------
    def mrz_checksum(self, data):

        weights = [7, 3, 1]

        total = 0

        for i, char in enumerate(data):

            if char.isdigit():
                val = int(char)

            elif char == "<":
                val = 0

            else:
                val = ord(char) - 55

            total += val * weights[i % 3]

        return total % 10
    def parse_mrz_date(self, date_str):

        year = int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:6])

        # Century logic
        if year > 30:
            year += 1900
        else:
            year += 2000

        return datetime(year, month, day)

    def normalize_mrz_line(self, line):

        # Remove spaces
        line = line.replace(" ", "")

        # If already correct
        if len(line) == 44:
            return line

         # Remove extra < from right
        while len(line) > 44 and "<" in line:

            idx = line.rfind("<")
            line = line[:idx] + line[idx+1:]

        # Pad if short
        if len(line) < 44:
            line = line.ljust(44, "<")

        return line[:44]
    
    # ---------------------------------------
    # Parse MRZ
    # ---------------------------------------
    def parse_mrz(self, lines):

        mrz_lines = []

        for line in lines:
             # Clean spaces
            line = line.replace(" ", "")

            # Match possible MRZ
            if re.fullmatch(r"[A-Z0-9<]{44,46}", line): # write one only accept 44 chars but we will normalize it to 44, allow some extra chars for OCR errors

                # Normalize to 44 chars
                fixed = self.normalize_mrz_line(line)

                if len(fixed) == 44:
                    mrz_lines.append(fixed)
                    
        print("[INFO] MRZ Candidates:", mrz_lines)
        
        if len(mrz_lines) < 2:
            return None

        l1 = mrz_lines[-2]
        l2 = mrz_lines[-1]

        # Validate length
        if len(l1) != 44 or len(l2) != 44:
            return None

        # Checksum validation
        passport_no = l2[0:9]
        # passport_cd = l2[9]

        # if self.mrz_checksum(passport_no) != int(passport_cd):
        #     return None

        dob = l2[13:19]
        dob_cd = l2[19]

        # if self.mrz_checksum(dob) != int(dob_cd):
        #     return None

        expiry = l2[21:27]
        exp_cd = l2[27]

        # if self.mrz_checksum(expiry) != int(exp_cd):
        #     return None

        # Parse Name
        name_raw = l1[5:].replace("<", " ")
        parts = name_raw.split("  ")

        surname = parts[0].strip()
        given = parts[1].strip() if len(parts) > 1 else ""

        dob_dt = self.parse_mrz_date(dob)
        exp_dt = self.parse_mrz_date(expiry)

        result = {
            "document_type": l1[0],
            "country": l1[2:5],
            "surname": surname,
            "given_name": given,
            "passport_number": passport_no,
            "nationality": l2[10:13],
            "date_of_birth": dob_dt.strftime("%Y-%m-%d"),
            "gender": l2[20],
            "expiry_date": exp_dt.strftime("%Y-%m-%d")
        }

        return result

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

        print("[INFO] OCR Lines:", lines)
        
        if not lines:

            self.delete_from_s3(filename)
            os.remove(temp_file)
            return {"status": "failed", "reason": "ocr_failed"}

        # ----------------------------
        # Step 5: Passport Check
        # ----------------------------

        if not self.is_passport_document(lines):

            self.delete_from_s3(filename)

            return {"status": "failed", "reason": "not_passport"}

        # ----------------------------
        # Step 6: MRZ
        # ----------------------------

        mrz_data = self.parse_mrz(lines)

        if mrz_data:
            passport_no = mrz_data["passport_number"]
        else:
            passport_no = self.extract_passport_number(lines)

        if not mrz_data:

            self.delete_from_s3(filename)
            os.remove(temp_file)
            return {"status": "failed", "reason": "invalid_mrz"}

        # ----------------------------
        # Cleanup temp file
        # ----------------------------

        try:
            confidence = self.calculate_confidence(
                lines=lines,
                mrz_data=mrz_data
            )

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
            "passport_number": passport_no,
            "mrz_data": mrz_data,
            "confidence": confidence
        }
