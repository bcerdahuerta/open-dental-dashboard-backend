"""
Data Ingestion Script: Sync Google Sheets to Dashboard Database.

This script fetches appointment data from clinic-specific Google Sheets
and upserts it into the PostgreSQL database via the Service Layer.

Usage:
    python -m scripts.sync_sheets
"""
import os
import sys

# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from datetime import datetime

from app import create_app
from models import Client, Clinic
from modules.clients.services.services import AppointmentService
from shared.gsheet_functions import gsheet_connection, read_gsheet
from shared.loggers import DentalRobotLogger


# Column index mapping based on context.md standard spreadsheet schema
# These indices should match the actual spreadsheet layout
COLUMN_MAP = {
    'practice': 0,              # Practice (Clinic Name)
    'carrier_name': 1,          # Carrier Name
    'member_id': 2,             # MemberID
    'subscriber_zip': 3,        # Subscriber Zip Code
    'subscriber_first_name': 4, # Subscriber First Name
    'subscriber_last_name': 5,  # Subscriber Last Name
    'subscriber_dob': 6,        # Subscriber DOB
    'patient_first_name': 7,    # Patient First Name
    'patient_last_name': 8,     # Patient Last Name
    'patient_dob': 9,           # Patient DOB
    'relationship': 10,         # Relationship to Subscriber
    'patnum': 11,               # PatNum (Open Dental Patient ID)
    'plannum': 12,              # Plannum (Open Dental Plan ID)
    'subscriber_patnum': 13,    # Subscriber Patnum
    'group_number': 14,         # Group Number
    'group_name': 15,           # Group Name
    'plan_type': 16,            # Plan Type
    'process_result': 17,       # Insurance Verification Process Result
    'verification_status': 18,  # Insurance Verification Status
    'verification_type': 19,    # Verification Type (FBD, ELG, Short Form)
    'upload_status': 20,        # Upload Status (PENDING, DONE, ERROR)
    'short_form_bks': 21,       # Short Form BKs (JSON/Text)
    'appointment_datetime': 22, # Appointment Datetime
    'file_url': 23,             # File URL (Drive PDF link)
    'update_status': 24,        # Update Status (Audit Status)
}


def safe_get(row: List[str], index: int, default: str = '') -> str:
    """Safely get a value from a row by index."""
    try:
        return row[index] if index < len(row) else default
    except (IndexError, TypeError):
        return default


def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse various date formats to datetime object."""
    if not date_str:
        return None
    
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%m/%d/%Y %H:%M',
        '%m/%d/%Y',
        '%Y-%m-%d',
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_date(date_str: str) -> Optional[str]:
    """Parse date string to YYYY-MM-DD format."""
    dt = parse_datetime(date_str)
    if dt:
        return dt.strftime('%Y-%m-%d')
    return None


def map_row_to_appointment(row: List[str], row_number: int) -> Dict[str, Any]:
    """
    Map a spreadsheet row to an appointment data dictionary.
    
    Args:
        row: List of cell values from the spreadsheet
        row_number: 1-indexed row number in the spreadsheet
        
    Returns:
        Dictionary matching AppointmentService.create_appointments_bulk schema
    """
    return {
        'spreadsheet_row': row_number,
        'practice': safe_get(row, COLUMN_MAP['practice']),
        'carrier_name': safe_get(row, COLUMN_MAP['carrier_name']),
        'patnum': safe_get(row, COLUMN_MAP['patnum']),
        'patient_first_name': safe_get(row, COLUMN_MAP['patient_first_name']),
        'patient_last_name': safe_get(row, COLUMN_MAP['patient_last_name']),
        'patient_dob': parse_date(safe_get(row, COLUMN_MAP['patient_dob'])),
        'appointment_datetime': safe_get(row, COLUMN_MAP['appointment_datetime']),
        'insurance_verification_status': safe_get(row, COLUMN_MAP['verification_status']),
        'insurance_verification_process_result': safe_get(row, COLUMN_MAP['process_result']),
        'verification_type': safe_get(row, COLUMN_MAP['verification_type']),
        'upload_status': safe_get(row, COLUMN_MAP['upload_status']),
        # Store extended data in raw_data via extras
        'member_id': safe_get(row, COLUMN_MAP['member_id']),
        'subscriber_first_name': safe_get(row, COLUMN_MAP['subscriber_first_name']),
        'subscriber_last_name': safe_get(row, COLUMN_MAP['subscriber_last_name']),
        'subscriber_dob': safe_get(row, COLUMN_MAP['subscriber_dob']),
        'relationship': safe_get(row, COLUMN_MAP['relationship']),
        'plannum': safe_get(row, COLUMN_MAP['plannum']),
        'group_number': safe_get(row, COLUMN_MAP['group_number']),
        'group_name': safe_get(row, COLUMN_MAP['group_name']),
        'plan_type': safe_get(row, COLUMN_MAP['plan_type']),
        'short_form_bks': safe_get(row, COLUMN_MAP['short_form_bks']),
        'file_url': safe_get(row, COLUMN_MAP['file_url']),
        'update_status': safe_get(row, COLUMN_MAP['update_status']),
    }


def sync_clinic_data(
    clinic_id: str,
    spreadsheet_id: str,
    token_path: str,
    credentials_path: str,
    logger: DentalRobotLogger
) -> int:
    """
    Sync Google Sheet data to appointments table.
    
    Args:
        clinic_id: The clinic's unique identifier
        spreadsheet_id: Google Sheets spreadsheet ID
        token_path: Path to token_sheet.pickle
        credentials_path: Path to credentials.json
        logger: DentalRobotLogger instance for this clinic
        
    Returns:
        Number of appointments synced
    """
    # Step 1: Establish Google Sheets connection
    try:
        if not os.path.exists(token_path):
            logger.error(f"Token file not found: {token_path}", save_log=True)
            return 0
            
        creds = gsheet_connection(token_path, credentials_path, logger)
        if not creds:
            logger.error("Failed to obtain credentials - Token may be expired", save_log=True)
            return 0
    except Exception as e:
        logger.error(f"Credential error: {str(e)}", save_log=True)
        return 0
    
    # Step 2: Read spreadsheet data
    try:
        # Read all data from Sheet1 (adjust range as needed for actual sheet layout)
        rows = read_gsheet(spreadsheet_id, "Sheet1!A:Z", creds, logger)
        if not rows:
            logger.warning(f"No data found in spreadsheet {spreadsheet_id}", save_log=True)
            return 0
    except Exception as e:
        logger.error(f"Error reading spreadsheet: {str(e)}", save_log=True)
        return 0
    
    # Step 3: Process rows (skip header row)
    appointments_data = []
    for idx, row in enumerate(rows[1:], start=2):  # start=2 for 1-indexed, skipping header
        # Skip empty rows
        if not row or not any(cell.strip() for cell in row if cell):
            continue
            
        # Skip rows without PatNum (required for patient resolution)
        patnum = safe_get(row, COLUMN_MAP['patnum'])
        if not patnum:
            logger.warning(f"Row {idx}: Missing PatNum, skipping", save_log=False)
            continue
            
        appointment = map_row_to_appointment(row, idx)
        appointments_data.append(appointment)
    
    if not appointments_data:
        logger.info("No valid appointments to sync", save_log=True)
        return 0
    
    # Step 4: Upsert via Service Layer
    try:
        result = AppointmentService.create_appointments_bulk(clinic_id, appointments_data)
        return len(result)
    except Exception as e:
        logger.error(f"Database error during bulk insert: {str(e)}", save_log=True)
        return 0


def main():
    """Main execution: sync all active clients' clinics."""
    app = create_app()
    
    with app.app_context():
        # Credential paths relative to app root
        token_path = os.path.join(app.root_path, '..', 'token_sheet.pickle')
        credentials_path = os.path.join(app.root_path, '..', 'credentials.json')
        
        # Normalize paths
        token_path = os.path.normpath(token_path)
        credentials_path = os.path.normpath(credentials_path)
        
        # Fetch all active clients
        clients = Client.query.filter_by(active=True).all()
        
        if not clients:
            print("[sync_sheets] No active clients found.")
            return
        
        print(f"[sync_sheets] Found {len(clients)} active client(s)")
        
        total_synced = 0
        
        for client in clients:
            # Iterate through each clinic with a spreadsheet_id
            for clinic in client.clinics:
                if not clinic.spreadsheet_id:
                    continue
                
                # Initialize logger for this clinic
                logger = DentalRobotLogger(
                    client_uid=client.id,
                    clinic_uid=clinic.id,
                    pipeline="sync_sheets"
                )
                
                logger.info(f"Starting sync for {clinic.clinic_name}", save_log=True)
                
                count = sync_clinic_data(
                    clinic_id=clinic.id,
                    spreadsheet_id=clinic.spreadsheet_id,
                    token_path=token_path,
                    credentials_path=credentials_path,
                    logger=logger
                )
                
                # Log result per constraint
                logger.info(
                    f"Synced {clinic.clinic_name}: {count} appointments.",
                    save_log=True
                )
                
                total_synced += count
        
        print(f"[sync_sheets] Complete. Total appointments synced: {total_synced}")


if __name__ == "__main__":
    main()
