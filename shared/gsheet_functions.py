from googleapiclient import discovery
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from .loggers import DentalRobotLogger


def gsheet_connection(token:str,credentials:str,logger:DentalRobotLogger):
    creds = None
    try:
        if os.path.exists(token):
            with open(token, 'rb') as token_file:
                creds = pickle.load(token_file)
            logger.warning("Token loaded successfully.", save_log=True)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logger.warning("Token refreshed successfully.", save_log=True)
                
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials, [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive.file',
                    'https://www.googleapis.com/auth/drive']
                    )
                creds = flow.run_local_server()
                logger.warning("Token created successfully.", save_log=True)
            with open(token, 'wb') as token_file:
                pickle.dump(creds, token_file)
            logger.warning("Token saved successfully.", save_log=True)
        return creds
    except HttpError as error:
        logger.error(f'An error occurred: {error}', save_log=True)

def read_gsheet(spreadsheet_id:str, range_name:str, creds,logger:DentalRobotLogger):
    try:
        service = discovery.build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        values = result.get('values', [])
        if len(values) == 0:
            logger.warning(f"No data found in {spreadsheet_id} in range {range_name}.", save_log=True)
            return None
        else:
            logger.info(f"Data was read successfully from {spreadsheet_id} in range {range_name}.", save_log=True)
            return values
    except HttpError as error:
        logger.error(f'An error occurred: {error}', save_log=True)

def create_gdrive_folder(folder_name:str, creds,logger:DentalRobotLogger):
    try:
        service = discovery.build('drive', 'v3', credentials=creds)
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        folder = service.files().create(body=file_metadata, fields='id').execute()
        logger.info(f"Folder {folder_name} created successfully.", save_log=True)
        folder_id = folder.get('id')
        if not folder_id:
            logger.error(f"Failed to create folder {folder_name}.", save_log=True)
            return None
        else:
            logger.info(f"Folder {folder_name} created successfully with ID: {folder_id}", save_log=True)
        return folder.get('id')
    except HttpError as error:
        logger.error(f'An error occurred: {error}', save_log=True)

def create_gsheet(spreadsheet_name: str, folder_id: str, creds,logger:DentalRobotLogger):
    try:
        if not folder_id:
            logger.error("Folder ID is None. Cannot create Google Sheet.", save_log=True)
            return None
        if not spreadsheet_name:
            logger.error("Spreadsheet name is None. Cannot create Google Sheet.", save_log=True)
            return None
        if not creds:
            logger.error("Credentials are None. Cannot create Google Sheet.", save_log=True)
            return None
        service = discovery.build('drive', 'v3', credentials=creds)
        file_metadata = {
            'name': spreadsheet_name,
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'parents': [folder_id]
        }
        sheet = service.files().create(body=file_metadata).execute()
        if not sheet:
            logger.error(f"Failed to create Google Sheet {spreadsheet_name}.", save_log=True)
            return None
        logger.info(f"Google Sheet {spreadsheet_name} created successfully with ID: {sheet.get('id')}", save_log=True)
        return sheet.get('id')
    except HttpError as error:
        logger.error(f'An error occurred: {error}', save_log=True)
        return None

def check_if_folder_exists(folder_name:str, creds,logger:DentalRobotLogger):
    try:
        if not creds:
            logger.error("Credentials are None. Cannot check folder existence.", save_log=True)
            return None
        if not folder_name:
            logger.error("Folder name is None. Cannot check folder existence.", save_log=True)
            return None
        service = discovery.build('drive', 'v3', credentials=creds)
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        results = service.files().list(q=query, fields="files(id)").execute()
        if not results:
            logger.warning(f"Folder {folder_name} does not exist.", save_log=True)
            return None
        items = results.get('files', [])
        if not items:
            logger.warning(f"Folder {folder_name} does not exist.", save_log=True)
            return None
        else:
            return items[0].get('id')
    except HttpError as error:
        logger.error(f'An error occurred: {error}', save_log=True)

def check_if_gsheet_exists(spreadsheet_name:str, folder_id:str, creds,logger:DentalRobotLogger):
    try:
        if not creds:
            logger.error("Credentials are None. Cannot check Google Sheet existence.", save_log=True)
            return None
        if not spreadsheet_name:
            logger.error("Spreadsheet name is None. Cannot check Google Sheet existence.", save_log=True)
            return None
        if not folder_id:
            logger.error("Folder ID is None. Cannot check Google Sheet existence.", save_log=True)
            return None
        service = discovery.build('drive', 'v3', credentials=creds)
        query = f"name='{spreadsheet_name}' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        results = service.files().list(q=query, fields="files(id)").execute()
        if not results:
            logger.warning(f"Google Sheet {spreadsheet_name} does not exist.", save_log=True)
            return None
        items = results.get('files', [])
        if not items:
            logger.warning(f"Google Sheet {spreadsheet_name} does not exist.", save_log=True)
            return None
        else:
            return items[0].get('id')
    except HttpError as error:
        logger.error(f'An error occurred: {error}', save_log=True)

