# import os
# import sys
# import base64
# import logging

# # Add src to path
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from src.services.face_liveness_service import face_liveness_service
# from src.workflows.kyc_engine.nodes.face import face_node

# logging.basicConfig(level=logging.INFO)

# def test_missing_images():
#     print("Testing face_node with missing images...")
#     state = {"raw_request": {}}
#     new_state = face_node(state)
#     print(f"Result: {new_state['face_check']}")
#     assert new_state["face_check"]["liveness_passed"] is False
#     assert "MISSING_IMAGES" in new_state["face_check"]["flags"]
#     print("Test passed!\n")

# def test_invalid_image_format():
#     print("Testing face_liveness_service with invalid image format...")
#     try:
#         face_liveness_service.verify_and_check_liveness("not_base64", "not_base64")
#     except Exception as e:
#         print(f"Caught expected exception: {e}")
#         print("Test passed!\n")

# if __name__ == "__main__":
#     print("Starting Face Liveness Verification Tests\n")
#     test_missing_images()
#     test_invalid_image_format()
#     print("Core logic verification complete. Actual DeepFace execution requires valid Base64 images and installed dependencies.")
