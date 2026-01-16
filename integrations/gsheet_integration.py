import os
import time
from shared.utils import LoadConfig, authenticate_and_get_token
from flask import jsonify, make_response, request
from shared.ccc_functions import get_data_from_endpoint
from shared.gsheet_functions import check_if_folder_exists, check_if_gsheet_exists, create_gsheet, gsheet_connection, create_gdrive_folder
from shared.loggers import DentalRobotLogger
from modules.clients.services.services import ClientService


def create_gsheet_book(client_uid: str, client_data: dict):
    log = {}

    token_sheet_path = os.environ.get('SHEET_PICKLE')
    creds_json = os.environ.get('GSHEET_CREDENTIALS_PATH')

    project_name = client_data.get("client_name")
    clinic_name = client_data.get("clinic_name")
    creds = gsheet_connection(token_sheet_path, creds_json, log)
    spreadsheet_name = f"{project_name} - {clinic_name}"
    folder_name = spreadsheet_name 

    clinic_folder_id = check_if_folder_exists(folder_name, creds, log)
    if not clinic_folder_id:
        clinic_folder_id = create_gdrive_folder((folder_name, creds, log))
        if clinic_folder_id is not None:
            make_response(jsonify({"message": "Clinic Folder created successfully"}), 200)
        else:
            make_response(jsonify({"error": "Failed to create clinic folder"}), 500)
    else:
        make_response(jsonify({"message": "Clinic Folder created successfully"}), 200)
        clinic_folder_id = clinic_folder_id

    spreadsheet_id = check_if_gsheet_exists(spreadsheet_name, clinic_folder_id, creds, log)

    if not spreadsheet_id:
        spreadsheet_id = create_gsheet(spreadsheet_name, clinic_folder_id, creds, log)
        if spreadsheet_id is not None:
            make_response(jsonify({"message": "Spreadsheet created successfully"}), 200)
            ClientService.update_client(client_uid, {"spreadsheet_id": spreadsheet_id})
        else:
            make_response(jsonify({"error": "Failed to create spreadsheet"}), 500)
    else:
        make_response(jsonify({"message": "Spreadsheet already exists"}), 200)