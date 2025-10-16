# attendance.py

import tkinter as tk
from tkinter import ttk, messagebox
import os
import logging
import threading  # <-- Import threading
import queue
from PIL import ImageTk, Image
import pyttsx3

# Project modules
import show_attendance
import takeImage
import trainImage
import automaticAttedance
import mongodb_handler
import settings
from utils import (setup_logging, apply_theme, BG_COLOR, FG_COLOR, BTN_BG,
                   BTN_FG, ACCENT_COLOR, TITLE_FONT, BTN_FONT, BASE_FONT, ERROR_COLOR)

# Initialize logging
setup_logging()

# --- Global Configuration ---
# Define paths for required directories and files
trainimage_path = "TrainingImage"
trainimagelabel_path = os.path.join("TrainingImageLabel", "Trainner.yml")
studentdetails_path = os.path.join("StudentDetails", "studentdetails.csv")
attendance_path = "Attendance"
ui_image_path = "UI_Image"

# Create necessary directories if they don't exist
os.makedirs(trainimage_path, exist_ok=True)
os.makedirs(os.path.dirname(trainimagelabel_path), exist_ok=True)
os.makedirs(os.path.dirname(studentdetails_path), exist_ok=True)
os.makedirs(attendance_path, exist_ok=True)

class AiAttendanceApp:
    """
    The main application class that creates and manages the UI.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Powered Attendance System")
        self.root.geometry("1280x720")
        apply_theme(self.root)

        # Check if UI images directory exists
        self.ui_images_exist = os.path.exists(ui_image_path)
        if not self.ui_images_exist:
            messagebox.showwarning("Warning", f"The '{ui_image_path}' directory is missing. Icons will not be displayed.")

        # Initialize the text-to-speech engine
        try:
            self.text_to_speech_engine = pyttsx3.init()
            self.tts_lock = threading.Lock() # <<< --- ADD THIS LINE ---
        except Exception as e:
            self.text_to_speech_engine = None
            logging.error(f"Could not initialize text-to-speech engine: {e}")

        self.create_widgets()

    def speak(self, text):
        """
        Uses the text-to-speech engine to speak the given text in a separate thread.
        """
        if self.text_to_speech_engine:
            try:
                # Run TTS in a separate thread to avoid blocking the UI
                threading.Thread(target=self._speak_thread, args=(text,), daemon=True).start()
            except Exception as e:
                logging.error(f"Text-to-speech failed: {e}")

    def _speak_thread(self, text):
        """Helper function that runs in a thread to handle speech synthesis."""
        # <<< --- REPLACE THE OLD _speak_thread WITH THIS ---
        with self.tts_lock: # Use the lock to ensure only one thread speaks at a time
            self.text_to_speech_engine.say(text)
            self.text_to_speech_engine.runAndWait()
        # --- END OF REPLACEMENT ---

    def create_widgets(self):
        """Creates and lays out all the widgets in the main application window."""
        header_frame = tk.Frame(self.root, bg=BG_COLOR)
        header_frame.pack(pady=20, fill=tk.X)
        
        # Add logo if UI images are available
        if self.ui_images_exist:
            try:
                logo_img = Image.open(os.path.join(ui_image_path, "0001.png")).resize((60, 60), Image.Resampling.LANCZOS)
                self.logo = ImageTk.PhotoImage(logo_img)
                tk.Label(header_frame, image=self.logo, bg=BG_COLOR).pack(side=tk.LEFT, padx=(50, 20))
            except Exception as e:
                logging.error(f"Failed to load logo: {e}")

        tk.Label(header_frame, text="Ai Attendance", font=TITLE_FONT, bg=BG_COLOR, fg=ACCENT_COLOR).pack(side=tk.LEFT)

        # Main content frame for the primary action buttons
        content_frame = tk.Frame(self.root, bg=BG_COLOR)
        content_frame.pack(expand=True, fill=tk.BOTH, padx=50, pady=20)

        # Create main action buttons
        self.create_main_button(content_frame, "Register Student", os.path.join(ui_image_path, "register.png"), self.open_register_window)
        self.create_main_button(content_frame, "Take Attendance", os.path.join(ui_image_path, "attendance.png"), self.open_attendance_window)
        self.create_main_button(content_frame, "View Attendance", os.path.join(ui_image_path, "verifyy.png"), self.open_view_window)
        self.create_main_button(content_frame, "Settings", os.path.join(ui_image_path, "setting.png"), self.open_settings_window)

        # Footer frame for sync button, status, and exit
        footer_frame = tk.Frame(self.root, bg=BG_COLOR)
        footer_frame.pack(side=tk.BOTTOM, pady=20, fill=tk.X)

        self.sync_status_label = tk.Label(footer_frame, text="", font=("Verdana", 10), bg=BG_COLOR, fg=FG_COLOR)
        self.sync_status_label.pack()

        action_buttons_frame = tk.Frame(footer_frame, bg=BG_COLOR)
        action_buttons_frame.pack(expand=True)

        self.sync_button = tk.Button(action_buttons_frame, text="Sync Pending Records", command=self.sync_pending_threaded, font=BTN_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT, bd=0, padx=20, pady=10)
        self.sync_button.pack(side=tk.LEFT, padx=10)

        tk.Button(action_buttons_frame, text="Exit", command=self.root.quit, font=BTN_FONT, bg=ERROR_COLOR, fg="white", relief=tk.FLAT, bd=0, padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    def create_main_button(self, parent, text, img_path, command):
        """Helper function to create the large icon buttons on the main screen."""
        frame = tk.Frame(parent, bg=BG_COLOR)
        frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        btn = tk.Button(frame, text=text, command=command, font=BTN_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT, bd=0, width=20, pady=15, compound=tk.TOP)
        
        if self.ui_images_exist:
            try:
                btn_img = Image.open(img_path).resize((128, 128), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(btn_img)
                btn.config(image=img)
                btn.image = img # Keep a reference
            except Exception as e:
                logging.warning(f"Button image not found: {img_path}. Error: {e}")
        
        btn.pack(fill=tk.X)

    def open_register_window(self):
        """Opens the student registration window."""
        RegisterStudentWindow(tk.Toplevel(self.root), self)

    def open_attendance_window(self):
        """Opens the attendance taking window."""
        automaticAttedance.subjectChoose(self)

    def open_view_window(self):
        """Opens the attendance viewing window."""
        show_attendance.subjectchoose(self)
        
    def open_settings_window(self):
        """Opens the application settings window."""
        settings.SettingsWindow(tk.Toplevel(self.root), self)

    def sync_pending_threaded(self):
        """
        Starts the process of syncing pending offline attendance records to MongoDB in a new thread.
        """
        self.sync_button.config(state=tk.DISABLED, text="Syncing...")
        self.update_sync_status("Starting sync...")
        threading.Thread(target=mongodb_handler.sync_pending_files, args=(self.update_sync_status,), daemon=True).start()

    def update_sync_status(self, message):
        """Updates the sync status label on the main window. This is a callback for the sync thread."""
        self.sync_status_label.config(text=message)
        # Re-enable the button once syncing is complete or if there was nothing to sync
        if any(keyword in message.lower() for keyword in ["complete", "no pending", "empty", "failed", "configured"]):
            self.sync_button.config(state=tk.NORMAL, text="Sync Pending Records")

class RegisterStudentWindow:
    """
    A window for registering new students by capturing their photos and training the recognition model.
    """
    def __init__(self, window, app):
        self.window = window
        self.app = app
        self.window.title("Register New Student")
        # A thread-safe queue to receive messages from worker threads
        self.queue = queue.Queue()
        self.is_capture_successful = False

        apply_theme(self.window)
        self.window.geometry("780x520")
        self.window.resizable(False, False)
        
        self.create_widgets()
        # Start polling the queue for messages from threads
        self.process_queue()

    def create_widgets(self):
        """Creates and lays out the widgets for the registration window."""
        title = tk.Label(self.window, text="Register Your Face", font=("Verdana", 24, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        title.pack(pady=20)
        
        input_frame = tk.Frame(self.window, bg=BG_COLOR)
        input_frame.pack(pady=10, padx=50, fill=tk.X)
        
        tk.Label(input_frame, text="Enrollment No:", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, sticky="w", pady=10, padx=5)
        self.txt_enroll = tk.Entry(input_frame, font=BTN_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT, width=30)
        self.txt_enroll.grid(row=0, column=1, sticky="ew")

        tk.Label(input_frame, text="Student Name:", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=0, sticky="w", pady=10, padx=5)
        self.txt_name = tk.Entry(input_frame, font=BTN_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT, width=30)
        self.txt_name.grid(row=1, column=1, sticky="ew")
        input_frame.grid_columnconfigure(1, weight=1)

        progress_frame = tk.Frame(self.window, bg=BG_COLOR)
        progress_frame.pack(pady=20, padx=50, fill=tk.X)
        
        tk.Label(progress_frame, text="Capture Progress:", font=BASE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w")
        self.progress_capture = ttk.Progressbar(progress_frame, style="yellow.Horizontal.TProgressbar", length=100, mode='determinate')
        self.progress_capture.pack(fill=tk.X, pady=(5, 15))

        tk.Label(progress_frame, text="Training Progress:", font=BASE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(anchor="w")
        self.progress_train = ttk.Progressbar(progress_frame, style="yellow.Horizontal.TProgressbar", length=100, mode='determinate')
        self.progress_train.pack(fill=tk.X, pady=5)
        
        btn_frame = tk.Frame(self.window, bg=BG_COLOR)
        btn_frame.pack(pady=20, padx=50, fill=tk.X)

        self.btn_capture = tk.Button(btn_frame, text="1. Capture Images", command=self.capture_threaded, font=BTN_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT, padx=15, pady=10)
        self.btn_capture.pack(side=tk.LEFT, expand=True, padx=10)

        self.btn_train = tk.Button(btn_frame, text="2. Train Model", command=self.train_threaded, font=BTN_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT, padx=15, pady=10, state=tk.DISABLED)
        self.btn_train.pack(side=tk.RIGHT, expand=True, padx=10)
        
        self.status_label = tk.Label(self.window, text="", font=BASE_FONT, bg=BG_COLOR, fg=FG_COLOR, wraplength=700)
        self.status_label.pack(pady=10)

    def process_queue(self):
        """
        Processes messages from the worker threads (capture/train) to update the UI.
        This runs periodically on the main UI thread.
        """
        try:
            message = self.queue.get_nowait()
            msg_type = message.get("type")
            
            if msg_type == "progress_capture":
                self.progress_capture['value'] = message.get("value", 0)
            elif msg_type == "progress_train":
                self.progress_train['value'] = message.get("value", 0)
            elif msg_type == "status":
                self.set_status(message.get("text", ""), message.get("is_error", False))
            elif msg_type == "capture_complete":
                self.is_capture_successful = message.get("success", False)
                self.toggle_buttons(tk.NORMAL) # Re-enable buttons
                if self.is_capture_successful:
                    self.set_status("Capture successful. You can now train the model.")
                else:
                    self.set_status("Capture failed. Please check the camera and try again.", is_error=True)
            elif msg_type == "train_complete":
                self.toggle_buttons(tk.NORMAL) # Re-enable buttons
                if message.get("success"):
                    self.set_status("Model training successful! You can now take attendance.")
                else:
                    self.set_status("Model training failed. Please check the logs for details.", is_error=True)

        except queue.Empty:
            # No messages in the queue, do nothing
            pass
        finally:
            # Schedule the next check
            self.window.after(100, self.process_queue)

    def capture_threaded(self):
        """
        Validates input and starts the image capture process in a separate thread.
        """
        enrollment = self.txt_enroll.get().strip()
        name = self.txt_name.get().strip()
        if not enrollment.isdigit() or not name:
            self.set_status("Enrollment must be a number and Name is required.", is_error=True)
            return

        # Disable buttons and reset state
        self.toggle_buttons(tk.DISABLED)
        self.is_capture_successful = False
        self.progress_capture['value'] = 0
        self.progress_train['value'] = 0

        # Start the capture process in a daemon thread
        threading.Thread(
            target=takeImage.TakeImage, 
            args=(enrollment, name, trainimage_path, studentdetails_path, self.queue), 
            daemon=True
        ).start()

    def train_threaded(self):
        """
        Starts the model training process in a separate thread.
        """
        self.toggle_buttons(tk.DISABLED)
        self.progress_train['value'] = 0
        
        # Start the training process in a daemon thread
        threading.Thread(
            target=trainImage.TrainImage, 
            args=(trainimage_path, trainimagelabel_path, self.queue), 
            daemon=True
        ).start()

    def toggle_buttons(self, state):
        """
        Enables or disables the main action buttons in the window.
        """
        self.btn_capture.config(state=state)
        # The train button should only be enabled if capture was successful
        if state == tk.NORMAL and self.is_capture_successful:
            self.btn_train.config(state=tk.NORMAL)
        else:
            self.btn_train.config(state=tk.DISABLED)

    def set_status(self, text, is_error=False):
        """
        Updates the status label with a message and optionally speaks it.
        """
        color = ERROR_COLOR if is_error else FG_COLOR
        self.status_label.config(text=text, fg=color)
        if text and not is_error:
            self.app.speak(text)

if __name__ == "__main__":
    root = tk.Tk()
    app = AiAttendanceApp(root)
    root.mainloop()