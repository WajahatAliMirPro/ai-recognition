# trainImage.py

import os
import cv2
import numpy as np
import logging
from PIL import Image

def TrainImage(train_path, label_path, q):
    """
    Trains the LBPH face recognizer with the captured images.
    This function is designed to run in a separate thread.

    Args:
        train_path (str): The root directory containing training images.
        label_path (str): The file path to save the trained model (.yml).
        q (queue.Queue): A queue to send progress and status updates to the UI.
    """
    success = False
    try:
        q.put({"type": "status", "text": "Loading images for training..."})
        q.put({"type": "progress_train", "value": 0})
        
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        faces, ids = get_images_and_labels(train_path, q)
        
        if not faces:
            raise ValueError("No images found to train. Please capture images for at least one student first.")

        # This part can be slow, so we inform the user.
        q.put({"type": "status", "text": f"Training model on {len(faces)} images... This may take a moment."})
        # The actual training happens here.
        recognizer.train(faces, np.array(ids))
        
        # We assume training takes the remaining 50% of the progress bar.
        q.put({"type": "progress_train", "value": 100})
        
        # Save the trained model to the specified file.
        os.makedirs(os.path.dirname(label_path), exist_ok=True)
        recognizer.save(label_path)
        
        success = True
        
    except Exception as e:
        logging.error(f"Error during training: {e}", exc_info=True)
        q.put({"type": "status", "text": f"Error during training: {e}", "is_error": True})
        success = False
    finally:
        # Notify the UI that training is complete.
        q.put({"type": "train_complete", "success": success})

def get_images_and_labels(path, q):
    """
    Reads all image files from the training path, extracts face data and student IDs.
    """
    # Find all image paths recursively in the training directory.
    image_paths = [os.path.join(dirpath, f)
                   for dirpath, dirnames, filenames in os.walk(path)
                   for f in filenames if f.endswith(('.jpg', '.png'))]
    
    faces, ids = [], []
    total_images = len(image_paths)
    
    if total_images == 0:
        return faces, ids

    for i, image_path in enumerate(image_paths):
        try:
            # Open the image in grayscale format.
            pil_image = Image.open(image_path).convert('L')
            image_np = np.array(pil_image, 'uint8')
            
            # Extract the student ID from the filename (e.g., Name_123_1.jpg -> 123)
            student_id = int(os.path.basename(image_path).split('_')[1])
            
            faces.append(image_np)
            ids.append(student_id)
            
            # Report progress for the image loading phase (0% to 50% of the bar).
            # This provides feedback to the user that something is happening.
            progress = ((i + 1) / total_images) * 50
            q.put({"type": "progress_train", "value": progress})
            if (i + 1) % 50 == 0: # Update status label periodically
                q.put({"type": "status", "text": f"Loading image {i+1}/{total_images}..."})

        except Exception as e:
            logging.warning(f"Skipping file {image_path} due to error: {e}")
            
    q.put({"type": "status", "text": f"Loaded {len(faces)} images. Now starting training..."})
    return faces, ids
