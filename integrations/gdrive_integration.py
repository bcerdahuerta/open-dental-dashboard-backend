import os
from flask import jsonify, make_response
from shared.gsheet_functions import gsheet_connection, check_if_folder_exists
from shared.loggers import DentalRobotLogger
from modules.clients.services.services import ClientService


def create_gdrive_folder(client_uid: str, client_data: dict):
    log = {}

    token_sheet_path = os.environ.get('SHEET_PICKLE')
    creds_json = os.environ.get('GSHEET_CREDENTIALS_PATH')

    if not os.path.exists(token_sheet_path):
        make_response(jsonify({"error": "Token file not found"}), 404)
    if not os.path.exists(creds_json):
        make_response(jsonify({"error": "Credentials file not found"}), 404)

    project_name = client_data.get("client_name")
    folder_name = project_name
    log["customer_id"] = project_name
    creds = gsheet_connection(token_sheet_path, creds_json, log)

    folder_id = check_if_folder_exists(folder_name, creds, log)

    if not folder_id:
        folder_id = create_gdrive_folder(folder_name, creds, log)
        if folder_id is not None:
            make_response(jsonify({"message": "Folder created successfully"}), 200)
            ClientService.update_client(client_uid, {"folder_id": folder_id})
        else:
            make_response(jsonify({"error": "Failed to create folder"}), 500)
    else:
        # Assuming log is a dict based on early initialization, though gsheet_connection might modify it.
        # But looking at line 9: log = {}
        if isinstance(log, dict):
            log["info"] = f"Folder {folder_name} already exists."
        else:
            log.info(f"Folder {folder_name} already exists.", save_log=True)
