# automaticAttedance.py

import tkinter as tk
import os
import cv2
import pandas as pd
import datetime
import time
import threading
import logging
import numpy as np
import mongodb_handler
from settings import load_settings
from utils import (apply_theme, BG_COLOR, FG_COLOR, BTN_BG, BTN_FG,
                   ACCENT_COLOR, BTN_FONT, BASE_FONT, ERROR_COLOR, SUCCESS_COLOR)

# --- DNN Model Configuration ---
PROTOTXT_PATH = "deploy.prototxt.txt"
WEIGHTS_PATH = "res10_300x300_ssd_iter_140000.caffemodel"
CONFIDENCE_THRESHOLD = 0.7  # Face detection confidence
RECOGNITION_CONFIDENCE = 75 # LBPH Face recognition confidence threshold (lower is better)

def subjectChoose(app):
    """Entry point function to create the attendance taker window."""
    AttendanceTakerWindow(tk.Toplevel(app.root), app)

class AttendanceTakerWindow:
    """
    A Tkinter window for starting and stopping the live attendance process.
    """
    def __init__(self, window, app):
        self.window = window
        self.app = app
        self.window.title("Take Attendance")
        self.window.geometry("600x400")
        apply_theme(self.window)
        self.window.resizable(False, False)
        self.attendance_thread = None
        self.stop_event = threading.Event()
        self.create_widgets()

    def create_widgets(self):
        """Creates and lays out the widgets for this window."""
        title = tk.Label(self.window, text="Start Live Attendance", font=("arial", 22, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        title.pack(pady=20)
        
        input_frame = tk.Frame(self.window, bg=BG_COLOR)
        input_frame.pack(pady=10, padx=40, fill=tk.X)
        
        # Subject Input
        tk.Label(input_frame, text="Subject:", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, sticky="w", pady=5)
        self.txt_subject = tk.Entry(input_frame, font=BTN_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT)
        self.txt_subject.grid(row=0, column=1, sticky="ew", pady=5)

        # Duration Input
        tk.Label(input_frame, text="Duration (mins):", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=0, sticky="w", pady=5)
        self.txt_duration = tk.Entry(input_frame, font=BTN_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT)
        self.txt_duration.grid(row=1, column=1, sticky="ew", pady=5)
        input_frame.grid_columnconfigure(1, weight=1)

        btn_frame = tk.Frame(self.window, bg=BG_COLOR)
        btn_frame.pack(pady=20)
        
        self.btn_start = tk.Button(btn_frame, text="Start Attendance", command=self.start_attendance, font=BTN_FONT, bg=SUCCESS_COLOR, fg="white", relief=tk.FLAT, padx=15, pady=10)
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="Stop Attendance", command=self.stop_attendance, font=BTN_FONT, bg=ERROR_COLOR, fg="white", relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(self.window, text="", font=BASE_FONT, bg=BG_COLOR, fg=FG_COLOR, wraplength=550)
        self.status_label.pack(pady=10)
        
        # Ensure thread is stopped if the window is closed
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def start_attendance(self):
        """Validates input and starts the attendance-taking thread."""
        subject = self.txt_subject.get().strip()
        duration_str = self.txt_duration.get().strip()

        if not subject:
            self.set_status("Please enter a subject name.", is_error=True)
            return

        try:
            duration_minutes = int(duration_str)
            if duration_minutes <= 0:
                self.set_status("Duration must be a positive number.", is_error=True)
                return
        except ValueError:
            self.set_status("Please enter a valid number for duration.", is_error=True)
            return

        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.stop_event.clear()
        
        # Create and start the attendance thread
        self.attendance_thread = threading.Thread(
            target=FillAttendance, 
            args=(subject, duration_minutes, self.stop_event, self.set_status, self.on_attendance_finish), 
            daemon=True
        )
        self.attendance_thread.start()
        
    def stop_attendance(self):
        """Signals the attendance thread to stop."""
        self.set_status("Stopping camera...")
        self.stop_event.set()
        
    def on_attendance_finish(self, message=""):
        """Callback function executed when the attendance thread finishes."""
        if message: self.set_status(message)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        
    def set_status(self, text, is_error=False):
        """Updates the status label in a thread-safe way."""
        color = ERROR_COLOR if is_error else FG_COLOR
        self.status_label.config(text=text, fg=color)
        if text: self.app.speak(text)
        
    def on_close(self):
        """Handles the window close event to ensure the thread is stopped cleanly."""
        if self.attendance_thread and self.attendance_thread.is_alive():
            self.stop_event.set()
            self.attendance_thread.join() # Wait for the thread to finish
        self.window.destroy()

def FillAttendance(subject, duration_minutes, stop_event, status_callback, on_finish_callback):
    """
    The core function for taking attendance. It runs in a separate thread.
    Opens the camera, detects and recognizes faces, and saves the attendance.
    """
    cam = None
    try:
        model_path = os.path.join("TrainingImageLabel", "Trainner.yml")
        details_path = os.path.join("StudentDetails", "studentdetails.csv")
        
        # Check for all required files before starting
        required_files = [model_path, details_path, PROTOTXT_PATH, WEIGHTS_PATH]
        if not all(os.path.exists(p) for p in required_files):
            raise FileNotFoundError("Model or details file missing. Please register students and train the model first.")
            
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        recognizer.read(model_path)
        net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, WEIGHTS_PATH)
        df_students = pd.read_csv(details_path)
        
        app_settings = load_settings()
        camera_index = app_settings.get("camera_index", 0)
        
        cam = cv2.VideoCapture(camera_index)
        if not cam.isOpened(): raise IOError(f"Cannot open webcam at index {camera_index}.")
            
        status_callback(f"Camera started for {duration_minutes} minute(s).")
        
        attendance = pd.DataFrame(columns=["Enrollment", "Name"])
        recognized_ids = set()
        
        window_name = "Live Attendance - Press 'Q' to Stop"
        start_time = time.time()
        duration_seconds = duration_minutes * 60
        
        while not stop_event.is_set():
            # Check for duration limit
            elapsed_time = time.time() - start_time
            if elapsed_time > duration_seconds:
                status_callback("Attendance session timed out.")
                break

            ret, im = cam.read()
            if not ret: break
            
            gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
            (h, w) = im.shape[:2]
            
            # --- Face Detection using DNN ---
            blob = cv2.dnn.blobFromImage(cv2.resize(im, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
            net.setInput(blob)
            detections = net.forward()

            for i in range(0, detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > CONFIDENCE_THRESHOLD:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (startX, startY, endX, endY) = box.astype("int")
                    
                    # Ensure coordinates are valid
                    (startX, startY) = (max(0, startX), max(0, startY))
                    (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

                    face_roi_gray = gray[startY:endY, startX:endX]
                    if face_roi_gray.size == 0: continue

                    # --- Face Recognition ---
                    student_id, conf = recognizer.predict(face_roi_gray)
                    
                    if conf < RECOGNITION_CONFIDENCE: # A match is found
                        try:
                            student_id_str = str(student_id)
                            student = df_students.loc[df_students["Enrollment"].astype(str) == student_id_str]
                            if not student.empty:
                                name = student["Name"].values[0]
                                display_text = f"{student_id}-{name}"
                                # Mark attendance only once per session
                                if student_id not in recognized_ids:
                                    recognized_ids.add(student_id)
                                    new_entry = pd.DataFrame([{"Enrollment": student_id, "Name": name}])
                                    attendance = pd.concat([attendance, new_entry], ignore_index=True)
                                    status_callback(f"Recognized: {name}")
                                
                                cv2.rectangle(im, (startX, startY), (endX, endY), (0, 255, 0), 2)
                                cv2.putText(im, display_text, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
                        except Exception as e:
                            logging.error(f"Error processing recognized student ID {student_id}: {e}")
                    else: # Unknown person
                        cv2.rectangle(im, (startX, startY), (endX, endY), (0, 0, 255), 2)
                        cv2.putText(im, "Unknown", (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
            
            # Display timer
            remaining_time = max(0, int(duration_seconds - elapsed_time))
            timer_text = f"Time Left: {remaining_time // 60:02}:{remaining_time % 60:02}"
            cv2.putText(im, timer_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow(window_name, im)
            
            if cv2.waitKey(1) == ord('q'): break
        
        # After the loop, save the attendance if any students were recognized
        if not attendance.empty:
            ts = time.time()
            date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            timestamp = datetime.datetime.fromtimestamp(ts).strftime("%H-%M-%S")
            
            path = os.path.join("Attendance", subject)
            os.makedirs(path, exist_ok=True)
            filename = os.path.join(path, f"{subject}_{date}_{timestamp}.csv")
            
            attendance.to_csv(filename, index=False)
            status_callback(f"Attendance saved to {os.path.basename(filename)}")
            
            # Try to upload to MongoDB
            mongodb_handler.upload_df_to_mongodb(attendance, subject, date.replace('-',':'), timestamp, filename)
        else:
            status_callback("No students were recognized during the session.")
            
    except Exception as e:
        logging.error(f"Error in FillAttendance: {e}", exc_info=True)
        status_callback(f"Error: {e}", is_error=True)
    finally:
        # Crucial cleanup: release camera and destroy windows
        if cam is not None and cam.isOpened(): cam.release()
        cv2.destroyAllWindows()
        # Notify the UI thread that the process has finished
        if on_finish_callback: on_finish_callback()
