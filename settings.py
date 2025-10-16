# settings.py

import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import logging
from utils import apply_theme, BG_COLOR, FG_COLOR, BTN_BG, BTN_FG, BTN_FONT, BASE_FONT, ACCENT_COLOR

SETTINGS_FILE = "settings.json"
DEFAULT_SETTINGS = {
    "camera_index": 0,
    "mongo_uri": "YOUR_MONGODB_CONNECTION_STRING_HERE"
}

def load_settings():
    """
    Loads settings from the JSON file. If file or key is missing, returns defaults.
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                # Ensure all default keys are present
                for key, value in DEFAULT_SETTINGS.items():
                    settings.setdefault(key, value)
                return settings
        except (json.JSONDecodeError, TypeError):
            logging.error("Settings file is corrupted. Using defaults.")
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings_data):
    """
    Saves the provided settings dictionary to the JSON file.
    """
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=4)
        return True
    except Exception as e:
        logging.error(f"Failed to save settings: {e}")
        return False

class SettingsWindow:
    """
    A Tkinter window for managing application settings, like camera index and MongoDB URI.
    """
    def __init__(self, window, app):
        self.window = window
        self.app = app
        self.window.title("Settings")
        self.window.geometry("680x400")
        apply_theme(self.window)
        self.window.resizable(False, False)
        
        self.settings = load_settings()
        self.create_widgets()
        
    def create_widgets(self):
        """Creates and lays out the widgets for the settings window."""
        title = tk.Label(self.window, text="Application Settings", font=("arial", 20, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
        title.pack(pady=20)
        
        main_frame = tk.Frame(self.window, bg=BG_COLOR)
        main_frame.pack(pady=10, padx=40, fill=tk.BOTH, expand=True)

        # Camera Index
        tk.Label(main_frame, text="Camera Index:", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=0, column=0, sticky="w", pady=10)
        self.camera_index_var = tk.StringVar(value=str(self.settings.get("camera_index", 0)))
        vcmd = (self.window.register(self.validate_integer), '%P')
        self.txt_camera_index = tk.Entry(main_frame, font=BASE_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT, 
                                         textvariable=self.camera_index_var, validate='key', validatecommand=vcmd)
        self.txt_camera_index.grid(row=0, column=1, sticky="ew", pady=10)

        # MongoDB URI
        tk.Label(main_frame, text="MongoDB URI:", font=BTN_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=1, column=0, sticky="w", pady=10)
        self.mongo_uri_var = tk.StringVar(value=self.settings.get("mongo_uri", ""))
        self.txt_mongo_uri = tk.Entry(main_frame, font=BASE_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT, 
                                      textvariable=self.mongo_uri_var, width=50)
        self.txt_mongo_uri.grid(row=1, column=1, sticky="ew", pady=10)
        
        main_frame.grid_columnconfigure(1, weight=1)

        tk.Button(self.window, text="Save Settings", command=self.save_and_close, font=BTN_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT, padx=15, pady=10).pack(side=tk.BOTTOM, pady=20)

    def validate_integer(self, value_if_allowed):
        """Validation function to ensure only digits are entered in the entry field."""
        return value_if_allowed.isdigit() or value_if_allowed == ""

    def save_and_close(self):
        """Saves the current settings and closes the window."""
        try:
            camera_index = int(self.camera_index_var.get())
            mongo_uri = self.mongo_uri_var.get().strip()
            
            self.settings["camera_index"] = camera_index
            self.settings["mongo_uri"] = mongo_uri

            if not mongo_uri or mongo_uri == DEFAULT_SETTINGS["mongo_uri"]:
                messagebox.showwarning("Warning", "MongoDB URI is not set. Cloud sync will be disabled.", parent=self.window)

            if save_settings(self.settings):
                messagebox.showinfo("Success", "Settings saved successfully.", parent=self.window)
                self.app.speak("Settings saved.")
                self.window.destroy()
            else:
                messagebox.showerror("Error", "Failed to save settings. Check logs for details.", parent=self.window)
        except ValueError:
            messagebox.showerror("Invalid Input", "Camera index must be a valid number.", parent=self.window)
