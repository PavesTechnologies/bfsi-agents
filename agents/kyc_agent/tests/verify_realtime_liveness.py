import cv2
import logging
import base64
import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from deepface import DeepFace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_realtime_liveness():
    """
    Detects face liveness in a real-time webcam feed.
    """
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        logger.error("Cannot open webcam. Please ensure it's connected and accessible.")
        return

    logger.info("Starting real-time face liveness detection. Press 'q' to quit.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            logger.error("Failed to grab frame.")
            break
            
        # Draw instructions
        cv2.putText(frame, "Press 'q' to quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        try:
            # We use enforce_detection=False so it doesn't crash if no face is found
            # anti_spoofing=True checks for liveness
            results = DeepFace.extract_faces(
                img_path=frame,
                anti_spoofing=True,
                enforce_detection=False,
                detector_backend='opencv'
            )
            
            for face_obj in results:
                facial_area = face_obj.get("facial_area", {})
                is_real = face_obj.get("is_real", False)
                confidence = face_obj.get("confidence", 0.0)
                
                # Check if a face was actually detected (if enforce_detection is False, 
                # DeepFace might return the whole image if no face is found)
                if confidence > 0.0 and 'x' in facial_area:
                    x = facial_area.get('x', 0)
                    y = facial_area.get('y', 0)
                    w = facial_area.get('w', 0)
                    h = facial_area.get('h', 0)
                    
                    # Green for real, Red for spoof
                    color = (0, 255, 0) if is_real else (0, 0, 255)
                    label = "Real" if is_real else "Spoof"
                    
                    # Draw bounding box and label
                    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                    cv2.putText(frame, f"{label} ({confidence:.2f})", (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                    
        except ValueError:
            # DeepFace raised an error (e.g., no face found)
            pass
        except Exception as e:
            logger.debug(f"Error processing frame: {e}")
            
        cv2.imshow("Real-time Face Liveness", frame)
        
        # Quit on 'q' press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("NOTE: DeepFace needs to download the anti-spoofing model weights on first run.")
    print("This might take a moment. Ensure you have an internet connection.")
    test_realtime_liveness()
