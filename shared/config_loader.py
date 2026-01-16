import os
from google.cloud import secretmanager
import yaml
import sys

def get_secret(project_id,secret_id):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")

def load_client_config(client_id, path=None, logger=None, project_id=""):
    if path:
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
                config["credentials"]["developer_key"] = get_secret(project_id,"developer_key_test")
                config["credentials"]["customer_key"] = get_secret(project_id, client_id)
                return config
        except Exception as e:
            if logger:
                logger.error(f"Error loading config from {path}: {e}", save_log=True)
            raise
    else:
        raise ValueError("Must provide either path or secret_id+project_id.")

def load_general_settings(path=None, logger=None):
    if path:
        try:
            with open(path, "r") as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            if logger:
                logger.error(f"Error loading config from {path}: {e}", save_log=True)
            raise
    else:
        raise ValueError("Must provide either path or secret_id+project_id.")