# utils.py

import logging
from tkinter import ttk
import os

# --- Application Configuration ---
APP_NAME = "Ai Attendance"
LOG_FILE = "app.log"

# --- UI Theme and Styling ---
# A modern dark theme color palette
BG_COLOR = "#212121"      # Main background
FG_COLOR = "#FFFFFF"      # Main text color
BTN_BG = "#333333"        # Button background
BTN_FG = "#feda00"        # Button text color (bright yellow)
ACCENT_COLOR = "#feda00"  # For highlights, progress bars
SUCCESS_COLOR = "#4CAF50" # Green for success messages
ERROR_COLOR = "#F44336"   # Red for error messages

# Font configuration
TITLE_FONT = ("Verdana", 28, "bold")
BASE_FONT = ("Verdana", 12)
BTN_FONT = ("Verdana", 14, "bold")

def setup_logging():
    """Configures centralized logging to a file."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='a'), # Append to the log file
            logging.StreamHandler() # Also log to console
        ]
    )

def apply_theme(window):
    """Applies a consistent style to Tkinter widgets."""
    window.configure(background=BG_COLOR)
    
    # Style for TTK widgets (like Progressbar and Treeview)
    style = ttk.Style()
    style.theme_use('clam') # 'clam' or 'alt' are good for custom styling

    # Progressbar style
    style.configure("yellow.Horizontal.TProgressbar",
                    troughcolor=BTN_BG,
                    background=ACCENT_COLOR,
                    bordercolor=BTN_BG,
                    lightcolor=ACCENT_COLOR,
                    darkcolor=ACCENT_COLOR)

    # Treeview style
    style.configure("Treeview",
                    background=BG_COLOR,
                    foreground=FG_COLOR,
                    fieldbackground=BG_COLOR,
                    rowheight=25,
                    font=BASE_FONT)
    style.configure("Treeview.Heading",
                    background=BTN_BG,
                    foreground=ACCENT_COLOR,
                    font=('Verdana', 12, 'bold'),
                    relief="flat")
    style.map('Treeview.Heading', relief=[('active','groove'),('pressed','sunken')])
    style.map('Treeview',
              background=[('selected', '#4a4a4a')],
              foreground=[('selected', ACCENT_COLOR)])
    
    # Scrollbar style
    style.configure("TScrollbar",
                    gripcount=0,
                    background=BTN_BG,
                    darkcolor=BTN_BG,
                    lightcolor=BTN_BG,
                    troughcolor=BG_COLOR,
                    bordercolor=BG_COLOR,
                    arrowcolor=FG_COLOR)
    style.map('TScrollbar',
          background=[('active', ACCENT_COLOR)])
