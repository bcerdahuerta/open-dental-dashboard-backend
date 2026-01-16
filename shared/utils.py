import requests
from json import load
import yaml
from .loggers import DentalRobotLogger
import datetime
from typing import Any


token = None
BASE_API = "https://carriers.dentalautomation.ai/api"


def authenticate_and_get_token(base_url, username, password, logger: DentalRobotLogger):
    """
    Autentica al usuario y obtiene el token de acceso.

    Args:
        base_url (str): URL base del API.
        username (str): Nombre de usuario.
        password (str): Contraseña del usuario.

    Returns:
        str: Token de acceso si la autenticación es exitosa.
        None: Si la autenticación falla.
    """
    signin_endpoint = f"{base_url}/signin"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "username": username,
        "password": password
    }

    try:
        response = requests.post(
            signin_endpoint, json=payload, headers=headers)
        if response.status_code == 200:
            token = response.json().get("token")
            # print("Autenticación exitosa. Token obtenido.")
            logger.info(
                "Authentication successful. Token obtained.", save_log=True)
            return token
        else:
            # print(f"Error en la autenticación: {response.status_code} - {response.text}")
            logger.error(
                f"Authentication failed: {response.status_code} - {response.text}", save_log=True)
            return None
    except requests.RequestException as e:
        # print(f"Error al conectar con el API: {e}")
        logger.info(f"Error connecting to the API: {e}", save_log=True)
        return None


def LoadConfig(path_config, logger: DentalRobotLogger):
    config_data = None
    if path_config.endswith(".yaml"):
        try:
            with open(path_config, 'r') as f:
                config_data = yaml.load(f, Loader=yaml.FullLoader)
            logger.info("Starting Installing process.", save_log=True)
            logger.info(
                "The config.yaml file was loaded successfully.", save_log=True)
        except Exception as e:
            logger.error(
                "There was an error loading the config.yaml file.", save_log=True)
            logger.critical(f"Critical error occurred.{e}", save_log=True)
            raise
    else:
        with open(path_config) as json_file:
            config_data = load(json_file)
    return config_data


def is_valid_email(email):
    """
    Validates the email format.
    Args:
        email (str): Email address to validate.
    Returns:
        bool: True if the email is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


def is_valid_phone(phone):
    """
    Validates the phone number format.
    Args:
        phone (str): Phone number to validate.
    Returns:
        bool: True if the phone number is valid, False otherwise.
    """
    import re
    pattern = r'^\d{10}$'
    return re.match(pattern, phone) is not None


def is_valid_password(password):
    """
    Validates the password format.
    Args:
        password (str): Password to validate.
    Returns:
        bool: True if the password is valid, False otherwise.
    """
    import re
    pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
    return re.match(pattern, password) is not None


def is_valid_username(username):
    """
    Validates the username format.
    Args:
        username (str): Username to validate.
    Returns:
        bool: True if the username is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z0-9_]+$'
    return re.match(pattern, username) is not None


def is_valid_address(name):
    """
    Validates the address format.
    Args:
        name (str): Address to validate.
    Returns:
        bool: True if the address is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z0-9\s.,-]+$'
    return re.match(pattern, name) is not None


def is_valid_city(name):
    """
    Validates the city format.
    Args:
        name (str): City to validate.
    Returns:
        bool: True if the city is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z\s]+$'
    return re.match(pattern, name) is not None


def is_valid_state(name):
    """
    Validates the state format.
    Args:
        name (str): State to validate.
    Returns:
        bool: True if the state is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z\s]+$'
    return re.match(pattern, name) is not None


def is_valid_zip_code(name):
    """
    Validates the zip code format.
    Args:
        name (str): Zip code to validate.
    Returns:
        bool: True if the zip code is valid, False otherwise.
    """
    import re
    pattern = r'^\d{5}(-\d{4})?$'
    return re.match(pattern, name) is not None


def is_valid_country(name):
    """
    Validates the country format.
    Args:
        name (str): Country to validate.
    Returns:
        bool: True if the country is valid, False otherwise.
    """
    import re
    pattern = r'^[a-zA-Z\s]+$'
    return re.match(pattern, name) is not None


def convert_to_utc_datetime(value: Any) -> datetime.datetime:
    """Converts a value to a timezone-aware UTC datetime object."""
    if isinstance(value, datetime.datetime):
        if value.tzinfo is None:  # Naive datetime
            return value.replace(tzinfo=datetime.timezone.utc)
        return value.astimezone(datetime.timezone.utc)

    if isinstance(value, str):
        try:
            # (2025-05-28T23:05:03.717149+00:00)
            dt_obj = datetime.datetime.fromisoformat(value)
            if dt_obj.tzinfo is None:
                return dt_obj.replace(tzinfo=datetime.timezone.utc)
            return dt_obj.astimezone(datetime.timezone.utc)
        except ValueError:
            pass
        try:  # Try parsing without timezone if previous failed
            dt_obj = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
            return dt_obj.replace(tzinfo=datetime.timezone.utc)
        except ValueError:
            pass

    raise ValueError(f"Could not convert {value} to datetime")
