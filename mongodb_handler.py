# mongodb_handler.py

import os
import logging
import pandas as pd
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ConfigurationError
from settings import load_settings
from utils import setup_logging

# Call setup_logging at the start
setup_logging()

DB_NAME = "AiAttendance"
OFFLINE_LOG_FILE = "offline_sync_log.txt"

def get_mongo_client():
    """Establishes connection to MongoDB using URI from settings."""
    settings = load_settings()
    mongo_uri = settings.get("mongo_uri")

    if not mongo_uri or mongo_uri == "YOUR_MONGODB_CONNECTION_STRING_HERE":
        logging.warning("MongoDB URI not configured in settings.")
        return None, "MongoDB URI not configured. Please set it in Settings."

    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        return client, None
    except (ConnectionFailure, ConfigurationError) as e:
        logging.error(f"MongoDB connection failed: {e}")
        return None, f"MongoDB connection failed: {e}"

def log_failed_upload(csv_file_path):
    """Logs the path of a CSV file that failed to upload."""
    try:
        with open(OFFLINE_LOG_FILE, "a") as f:
            f.write(csv_file_path + "\n")
        logging.warning(f"Logged {os.path.basename(csv_file_path)} for future sync.")
    except Exception as e:
        logging.error(f"Could not write to offline log file: {e}", exc_info=True)

def upload_df_to_mongodb(df, subject, date, timestamp, csv_file_path):
    """Uploads attendance DataFrame to MongoDB."""
    client, error_message = get_mongo_client()
    if not client:
        log_failed_upload(csv_file_path)
        return False

    try:
        db = client[DB_NAME]
        collection = db[subject]
        
        records = df.to_dict('records')
        documents = [
            {
                "enrollment": str(rec.get("Enrollment")),
                "name": rec.get("Name"),
                "subject": subject,
                "date": date,
                "timestamp": timestamp,
                "status": "Present"
            } for rec in records
        ]

        if documents:
            collection.insert_many(documents)
            logging.info(f"Successfully uploaded {len(documents)} records for {subject}.")
        client.close()
        return True

    except Exception as e:
        logging.error(f"Error during MongoDB upload: {e}", exc_info=True)
        log_failed_upload(csv_file_path)
        if client: client.close()
        return False

def sync_pending_files(status_callback):
    """Reads the log file and tries to sync pending attendance CSVs."""
    client, error_message = get_mongo_client()
    if not client:
        status_callback(error_message)
        return

    if not os.path.exists(OFFLINE_LOG_FILE):
        status_callback("No pending files to sync.")
        client.close()
        return

    with open(OFFLINE_LOG_FILE, 'r') as f:
        pending_files = list(set([line.strip() for line in f if line.strip()])) # Use set to get unique files

    if not pending_files:
        status_callback("Sync log is empty. All clear!")
        client.close()
        return

    successful_syncs = []
    failed_syncs = []
    total = len(pending_files)
    status_callback(f"Starting sync for {total} file(s)...")

    for idx, file_path in enumerate(pending_files):
        if not os.path.exists(file_path):
            logging.warning(f"File not found, removing from log: {file_path}")
            successful_syncs.append(file_path)
            continue

        try:
            filename = os.path.basename(file_path)
            parts = filename.replace('.csv', '').split('_')
            subject, date, timestamp = parts[0], parts[1], parts[2].replace('-', ':')
            
            df = pd.read_csv(file_path)
            status_callback(f"Syncing {idx+1}/{total}: {filename}")

            if upload_df_to_mongodb(df, subject, date, timestamp, file_path):
                successful_syncs.append(file_path)
            else:
                # upload_df already logs the failure, so we just add it to the list
                failed_syncs.append(file_path)
        except Exception as e:
            logging.error(f"Failed to process or upload {file_path}: {e}", exc_info=True)
            failed_syncs.append(file_path)
    
    # Rewrite the log file with only the files that failed to sync again
    with open(OFFLINE_LOG_FILE, 'w') as f:
        for file_path in failed_syncs:
            f.write(file_path + "\n")
            
    synced_count = len(successful_syncs)
    remaining_count = len(failed_syncs)
    status_callback(f"Sync complete. Synced: {synced_count}, Remaining: {remaining_count}.")
    client.close()
