# takeImage.py

import os
import cv2
import csv
import logging
import numpy as np
from settings import load_settings

# --- DNN Model Configuration ---
PROTOTXT_PATH = "deploy.prototxt.txt"
WEIGHTS_PATH = "res10_300x300_ssd_iter_140000.caffemodel"
CONFIDENCE_THRESHOLD = 0.7  # Increased for better quality captures

def TakeImage(enrollment, name, train_path, details_csv_path, q):
    """
    Captures and saves face images for a student using a webcam.
    This function is designed to run in a separate thread.

    Args:
        enrollment (str): The student's enrollment number.
        name (str): The student's name.
        train_path (str): The root directory to save training images.
        details_csv_path (str): Path to the CSV file to save student details.
        q (queue.Queue): A queue to send progress and status updates to the UI.
    """
    cam = None
    success = False
    try:
        # Check if model files exist
        if not os.path.exists(PROTOTXT_PATH) or not os.path.exists(WEIGHTS_PATH):
            raise FileNotFoundError("DNN model files (prototxt/caffemodel) not found.")
            
        q.put({"type": "status", "text": "Loading face detection model..."})
        net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, WEIGHTS_PATH)
        
        # Load settings to get the correct camera index
        app_settings = load_settings()
        camera_index = app_settings.get("camera_index", 0)
        q.put({"type": "status", "text": f"Initializing camera index {camera_index}..."})

        cam = cv2.VideoCapture(camera_index)
        if not cam.isOpened():
            raise IOError(f"Cannot open webcam at index {camera_index}. Check settings.")

        sample_num = 0
        max_samples = 60  # Number of images to capture
        
        # Create a specific directory for the student's images
        directory = f"{enrollment}_{name}"
        path = os.path.join(train_path, directory)
        os.makedirs(path, exist_ok=True)
        
        q.put({"type": "status", "text": "Look at the camera. Capturing images..."})
        q.put({"type": "progress_capture", "value": 0})

        while sample_num < max_samples:
            ret, img = cam.read()
            if not ret:
                q.put({"type": "status", "text": "Failed to grab frame from camera.", "is_error": True})
                break
            
            # --- Face Detection using DNN ---
            (h, w) = img.shape[:2]
            blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            net.setInput(blob)
            detections = net.forward()
            
            best_face = None
            max_confidence = 0
            
            # Find the best (highest confidence) face in the frame
            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > CONFIDENCE_THRESHOLD and confidence > max_confidence:
                    max_confidence = confidence
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    # Ensure the detected box is within the image boundaries
                    (startX, startY) = (max(0, startX), max(0, startY))
                    (endX, endY) = (min(w - 1, endX), min(h - 1, endY))
                    best_face = (startX, startY, endX - startX, endY - startY)

            if best_face is not None:
                (x, y, face_w, face_h) = best_face
                # Ensure the detected face region is valid
                if face_w > 0 and face_h > 0:
                    cv2.rectangle(img, (x, y), (x + face_w, y + face_h), (0, 255, 0), 2)
                    sample_num += 1
                    
                    # Convert to grayscale and save the cropped face
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    img_path = os.path.join(path, f"{name}_{enrollment}_{sample_num}.jpg")
                    cv2.imwrite(img_path, gray[y:y+face_h, x:x+face_w])
                    
                    # Update progress bar in the UI via the queue
                    q.put({"type": "progress_capture", "value": (sample_num / max_samples) * 100})

            # Display capture progress on the camera feed window
            cv2.putText(img, f"Images Captured: {sample_num}/{max_samples}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow("Capturing Face... (Press 'q' to exit)", img)
            
            # Allow quitting with the 'q' key
            if cv2.waitKey(100) & 0xFF == ord('q'):
                break
        
        # After the loop, check if any images were captured
        if sample_num > 0:
            # Save student details to the CSV file
            file_exists = os.path.isfile(details_csv_path)
            with open(details_csv_path, "a+", newline='') as csvFile:
                writer = csv.writer(csvFile)
                # Write header only if the file is new/empty
                if not file_exists or os.path.getsize(details_csv_path) == 0:
                    writer.writerow(["Enrollment", "Name"])
                writer.writerow([enrollment, name])
            success = True
            q.put({"type": "status", "text": f"Successfully captured {sample_num} images."})
        else:
            q.put({"type": "status", "text": "No faces were detected. Please try again.", "is_error": True})
            success = False

    except Exception as e:
        logging.error(f"Error in TakeImage: {e}", exc_info=True)
        q.put({"type": "status", "text": f"An error occurred: {e}", "is_error": True})
        success = False
    finally:
        # Crucial cleanup step: always release the camera and destroy windows
        if cam is not None and cam.isOpened():
            cam.release()
        cv2.destroyAllWindows()
        # Notify the UI that the capture process is complete
        q.put({"type": "capture_complete", "success": success})
