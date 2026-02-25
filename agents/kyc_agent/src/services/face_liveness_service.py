# import os
# import base64
# import tempfile
# import logging
# from typing import Dict, Any, Optional
# from deepface import DeepFace
# import cv2
# import numpy as np

# logger = logging.getLogger(__name__)

# class FaceLivenessService:
#     """
#     Service for Face Matching (Verification) and Liveness Detection (Anti-spoofing)
#     using DeepFace and open-source models.
#     """

#     def __init__(self, face_match_threshold: float = 0.4):
#         self.face_match_threshold = face_match_threshold
#         # Pre-load models if necessary, though DeepFace usually handles this lazily

#     def _decode_base64_to_temp_file(self, b64_str: str) -> str:
#         """
#         Decodes a base64 string and saves it to a temporary file.
#         Returns the path to the temporary file.
#         """
#         try:
#             # Remove header if present (e.g., data:image/jpeg;base64,)
#             if "," in b64_str:
#                 b64_str = b64_str.split(",")[1]
            
#             img_data = base64.b64decode(b64_str)
#             temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
#             temp_file.write(img_data)
#             temp_file.close()
#             return temp_file.name
#         except Exception as e:
#             logger.error(f"Error decoding base64 image: {str(e)}")
#             raise ValueError("Invalid image data provided")

#     def verify_and_check_liveness(
#         self, 
#         selfie_b64: str, 
#         id_card_b64: str
#     ) -> Dict[str, Any]:
#         """
#         Performs face verification (matching) and anti-spoofing.
#         """
#         selfie_path = None
#         id_card_path = None
        
#         try:
#             selfie_path = self._decode_base64_to_temp_file(selfie_b64)
#             id_card_path = self._decode_base64_to_temp_file(id_card_b64)

#             # 1. Face Verification (Selfie vs ID Card)
#             # Default model is VGG-Face, which is good for general matching
#             verification = DeepFace.verify(
#                 img1_path=selfie_path,
#                 img2_path=id_card_path,
#                 enforce_detection=False,
#                 detector_backend='opencv' # Fastest for basic use
#             )

#             # 2. Anti-spoofing (Liveness) on Selfie
#             # DeepFace has a built-in anti-spoofing module
#             liveness_results = DeepFace.extract_faces(
#                 img_path=selfie_path,
#                 anti_spoofing=True,
#                 enforce_detection=False,
#                 detector_backend='opencv'
#             )

#             liveness_passed = True
#             liveness_score = 1.0 # Placeholder if not explicitly provided
#             spoof_detected = False

#             if liveness_results:
#                 # DeepFace returns a list of detected faces, check the first one
#                 is_real = liveness_results[0].get("is_real", True)
#                 liveness_passed = bool(is_real)
#                 spoof_detected = not liveness_passed
#                 # DeepFace doesn't always provide a confidence score for liveness in the same way, 
#                 # but we can infer it or use 1.0/0.0
#                 liveness_score = 1.0 if liveness_passed else 0.0

#             return {
#                 "face_match_score": 1.0 - verification.get("distance", 1.0), # Convert distance to score
#                 "liveness_passed": liveness_passed,
#                 "liveness_score": liveness_score,
#                 "spoof_detected": spoof_detected,
#                 "face_threshold": self.face_match_threshold,
#                 "face_detection_confidence": verification.get("similarity_score", 0.0),
#                 "deepfake_score": 0.0, # DeepFace doesn't do deepfake detection out of the box
#                 "replay_attack_detected": spoof_detected,
#                 "flags": {}
#             }

#         except Exception as e:
#             logger.error(f"Error during face liveness check: {str(e)}")
#             # Fallback to a failure state if processing fails
#             return {
#                 "face_match_score": 0.0,
#                 "liveness_passed": False,
#                 "liveness_score": 0.0,
#                 "spoof_detected": True,
#                 "flags": {"error": str(e)}
#             }
#         finally:
#             # Cleanup temporary files
#             if selfie_path and os.path.exists(selfie_path):
#                 os.remove(selfie_path)
#             if id_card_path and os.path.exists(id_card_path):
#                 os.remove(id_card_path)

# face_liveness_service = FaceLivenessService()
