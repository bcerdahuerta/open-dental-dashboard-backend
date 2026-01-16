import requests
import json
from .loggers import DentalRobotLogger


def bulk_error_handler(response, logger: DentalRobotLogger):
    """
    Maneja errores en la respuesta de una solicitud POST.

    Args:
        response (requests.Response): Respuesta de la solicitud POST.

    Returns:
        None
    """
    if response.status_code == 400:
        logger.error(
            f"Error al agregar carrier bots: {response.status_code} - {response.text}", save_log=True)
        return None
    if response.status_code == 401:
        logger.error(
            f"Error de autenticación: {response.status_code} - {response.text}", save_log=True)
        return None
    if response.status_code == 403:
        logger.error(
            f"Acceso denegado: {response.status_code} - {response.text}", save_log=True)
        return None
    if response.status_code == 500:
        logger.error(
            f"Error interno del servidor: {response.status_code} - {response.text}", save_log=True)
        return None
    else:
        logger.error(
            f"Error inesperado: {response.status_code} - {response.text}", save_log=True)
        return None


def get_data_from_endpoint(base_url, token, endpoint, logger: DentalRobotLogger):
    """
    Obtiene datos de un endpoint usando el token de autenticación.

    Args:
        base_url (str): URL base del API.
        token (str): Token de autenticación.
        endpoint (str): Endpoint al que se desea acceder.

    Returns:
        dict: Datos obtenidos del endpoint si la solicitud es exitosa.
        None: Si la solicitud falla.
    """
    if not token:
        logger.error("Token no proporcionado.", save_log=True)
        return None
    if not base_url:
        logger.error("URL base no proporcionada.", save_log=True)
        return None
    if not endpoint:
        logger.error("Endpoint no proporcionado.", save_log=True)
        return None

    url = f"{base_url}{endpoint}"
    headers = {
        "Content-Type": "application/json",
        "x-access-token": token
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logger.info(
                "Peticion al endpoint {endpoint} exitosa.", save_log=True)
            # ! ahora el metodo retorna el status code para controlar el flujo
            return response.json(), response.status_code
        else:
            logger.error(
                f"Error al obtener datos: {response.status_code} - {response.text}", save_log=True)
            return None
    except requests.RequestException as e:
        logger.error(f"Error al conectar con el API: {e}", save_log=True)
        return None


def post_bots_to_clinics(BASE_API_URL: str, ADD_MULTI_CLINICS_ENDPOINT: str, token: str, clinics_ids: list, bots: dict, logger: DentalRobotLogger):
    """
    Agrega bots a múltiples clínicas.
    Args:
        BASE_API_URL (str): URL base del API.
        ADD_MULTI_CLINICS_ENDPOINT (str): Endpoint para agregar múltiples clínicas.
        token (str): Token de autenticación.
        clinics_ids (list): Lista de IDs de clínicas a las que se agregarán los bots.
        bots (dict): Diccionario con la configuración de los bots.
    """
    if not token:
        logger.error("Token no proporcionado.", save_log=True)
        return None
    if not BASE_API_URL:
        logger.error("URL base no proporcionada.", save_log=True)
        return None
    if not ADD_MULTI_CLINICS_ENDPOINT:
        logger.error("Endpoint no proporcionado.", save_log=True)
        return None
    if not clinics_ids:
        logger.error("IDs de clínicas no proporcionados.", save_log=True)
        return None
    if not bots:
        logger.error("Bots no proporcionados.", save_log=True)
        return None
    # URL del endpoint para agregar múltiples clínicas
    # * /clinicbots/add/multi
    url = f"{BASE_API_URL}{ADD_MULTI_CLINICS_ENDPOINT}"

    # Datos a enviar en el cuerpo de la solicitud
    # data = {
    #     "clinicIds": [
    #         "65ca8a09dbd93a588caaeb68"

    #     ],
    #     "verify": False,
    #     "bots": {
    #         "Aetna FEDVIP": {
    #             "historyPrint": True,
    #             "username": "ffff",
    #             "password": "lets_bookmark",
    #             "isSharedRegExp": True,
    #             "regex": "(?i)^ADN*",
    #             "bot": "670fe89ad817afaae12140ee"
    #         }
    #     }
    # }
    data = {
        "clinicIds": clinics_ids,
        "verify": False,
        "bots": bots
    }
    # Encabezados de la solicitud
    headers = {
        "Content-Type": "application/json",
        "x-access-token": token
    }

    # Realizar la solicitud POST
    response = requests.post(url, json=data, headers=headers)
    # Verificar el estado de la respuesta
    if response.status_code == 200:
        logger.info("Carrier bots agregados exitosamente.", save_log=True)
        return response.json(), response.status_code
    bulk_error_handler(response, logger)
