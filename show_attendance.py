# show_attendance.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from glob import glob
import os
import logging
import datetime
from utils import (apply_theme, BG_COLOR, FG_COLOR, BTN_BG, BTN_FG,
                   ACCENT_COLOR, BTN_FONT, BASE_FONT)

def subjectchoose(app):
    ViewAttendanceWindow(tk.Toplevel(app.root), app)

class ViewAttendanceWindow:
    def __init__(self, window, app):
        self.window = window
        self.app = app
        self.window.title("View Attendance")
        self.window.geometry("800x600")
        apply_theme(self.window)
        
        self.df = None # To store the currently displayed dataframe for export
        self.create_widgets()
        
    def create_widgets(self):
        # --- Top Frame for Controls ---
        controls_frame = tk.Frame(self.window, bg=BG_COLOR)
        controls_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Subject
        tk.Label(controls_frame, text="Subject:", font=BASE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        self.txt_subject = tk.Entry(controls_frame, font=BASE_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT)
        self.txt_subject.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        # Date Filter
        tk.Label(controls_frame, text="Date (YYYY-MM-DD):", font=BASE_FONT, bg=BG_COLOR, fg=FG_COLOR).pack(side=tk.LEFT, padx=(10, 5))
        self.txt_date = tk.Entry(controls_frame, font=BASE_FONT, bg=BTN_BG, fg=FG_COLOR, relief=tk.FLAT, width=15)
        self.txt_date.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        self.btn_show = tk.Button(controls_frame, text="Show", command=self.show_attendance, font=BASE_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT)
        self.btn_show.pack(side=tk.LEFT, padx=10)
        
        self.btn_export = tk.Button(controls_frame, text="Export CSV", command=self.export_csv, font=BASE_FONT, bg=BTN_BG, fg=BTN_FG, relief=tk.FLAT, state=tk.DISABLED)
        self.btn_export.pack(side=tk.LEFT, padx=5)

        # --- Treeview Frame ---
        tree_frame = tk.Frame(self.window, bg=BG_COLOR)
        tree_frame.pack(expand=True, fill='both', padx=20, pady=10)

        self.tree = ttk.Treeview(tree_frame, style="Treeview")
        self.tree["show"] = "headings"

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        vsb.pack(side='right', fill='y')
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(expand=True, fill='both')

    def show_attendance(self):
        subject = self.txt_subject.get().strip()
        filter_date = self.txt_date.get().strip()

        if not subject:
            messagebox.showerror("Error", "Please enter a subject name.", parent=self.window)
            return

        attendance_folder = f"Attendance/{subject}"
        if not os.path.exists(attendance_folder):
            messagebox.showinfo("Not Found", f"No records found for subject '{subject}'.", parent=self.window)
            return

        try:
            csv_files = glob(os.path.join(attendance_folder, "*.csv"))
            if not csv_files:
                messagebox.showinfo("Not Found", f"No attendance sheets found for '{subject}'.", parent=self.window)
                return

            all_dfs = []
            for f in csv_files:
                try:
                    # Extract date from filename: Subject_YYYY-MM-DD_HH-MM-SS.csv
                    date_part = os.path.basename(f).split('_')[1]
                    # Filter by date if provided
                    if filter_date and date_part != filter_date:
                        continue
                    
                    df_file = pd.read_csv(f)
                    df_file['Date'] = date_part # Add date column
                    df_file['Timestamp'] = os.path.basename(f).split('_')[2].replace('.csv', '')
                    all_dfs.append(df_file)
                except IndexError:
                    logging.warning(f"Could not parse filename: {f}. Skipping.")
                    continue

            if not all_dfs:
                messagebox.showinfo("No Records", f"No records found for the specified date.", parent=self.window)
                self.clear_treeview()
                return

            merged_df = pd.concat(all_dfs, ignore_index=True)
            # Reorder columns for better display
            cols = ['Date', 'Timestamp', 'Enrollment', 'Name']
            merged_df = merged_df[cols].drop_duplicates().sort_values(by=['Date', 'Timestamp', 'Name'])
            
            self.df = merged_df # Store for export
            self.display_in_treeview(merged_df, subject)

        except Exception as e:
            logging.error(f"Error reading files for {subject}: {e}", exc_info=True)
            messagebox.showerror("Error", f"An error occurred: {e}", parent=self.window)

    def display_in_treeview(self, df, subject_name):
        self.clear_treeview()
        
        self.tree["columns"] = list(df.columns)
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor='center', width=150)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))
        
        if not df.empty:
            self.btn_export.config(state=tk.NORMAL)
        else:
            self.btn_export.config(state=tk.DISABLED)

    def clear_treeview(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.tree["columns"] = ()
        self.btn_export.config(state=tk.DISABLED)
        self.df = None

    def export_csv(self):
        if self.df is None or self.df.empty:
            messagebox.showwarning("No Data", "There is no data to export.", parent=self.window)
            return
        
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Attendance As",
                initialfile=f"attendance_{self.txt_subject.get().strip()}.csv"
            )
            if file_path:
                self.df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Data exported successfully to\n{file_path}", parent=self.window)
                self.app.speak("Data exported successfully.")
        except Exception as e:
            logging.error(f"Failed to export CSV: {e}", exc_info=True)
            messagebox.showerror("Export Error", f"An error occurred during export:\n{e}", parent=self.window)
