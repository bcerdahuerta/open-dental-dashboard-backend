from flask import Response, jsonify, make_response
from models import Client, Clinic, ClientConfig, Task


def get_config_by_clinic_id(client_uuid, clinic_uuid, config_name):
    """
    Get Config by Clinic
    ---
    tags:
      - Configs
    parameters:
      - in: path
        name: client_uuid
        type: string
        required: true
      - in: path
        name: clinic_uuid
        type: string
        required: true
      - in: path
        name: config_name
        type: string
        required: true
    responses:
      200:
        description: YAML content
      404:
        description: Config not found
    """
    if client_uuid and clinic_uuid and config_name:
        config = ClientConfig.query.filter_by(
            client_id=client_uuid,
            clinic_id=clinic_uuid,
            config_name=config_name
        ).first()

        if config and config.yaml_content:
            return Response(config.yaml_content, mimetype='text/yaml')

    return Response("Configuración no encontrada", status=404)


def get_clinics_by_client_id(client_uuid):
    """
    Get Clinics by Client
    ---
    tags:
      - Clinics
    parameters:
      - in: path
        name: client_uuid
        type: string
        required: true
    responses:
      200:
        description: List of clinics
      404:
        description: Client not found
    """
    # Verify client exists
    client = Client.query.get(client_uuid)
    if not client:
        return make_response(jsonify({
            "message": f"Cliente con client_uid '{client_uuid}' no encontrado."
        }), 404)

    # Query clinics by client_id
    clinics = Clinic.query.filter_by(client_id=client_uuid).all()

    clinics_list = []
    for clinic in clinics:
        clinic_data = clinic.to_dict()
        if "clinic_uid" not in clinic_data:
            clinic_data["clinic_uid"] = clinic.id
        clinics_list.append(clinic_data)

    return jsonify(clinics_list)


def get_clinic_by_uuid_for_client(client_uuid, clinic_uuid):
    """
    Get Clinic Details
    ---
    tags:
      - Clinics
    parameters:
      - in: path
        name: client_uuid
        type: string
        required: true
      - in: path
        name: clinic_uuid
        type: string
        required: true
    responses:
      200:
        description: Clinic details
      404:
        description: Clinic not found
    """
    # Try to find client by ID first
    client = Client.query.get(client_uuid)
    if not client:
        return make_response(jsonify({
            "message": f"Cliente '{client_uuid}' no encontrado."
        }), 404)

    # Find clinic
    clinic = Clinic.query.filter_by(id=clinic_uuid, client_id=client_uuid).first()

    if clinic:
        clinic_data = clinic.to_dict()
        clinic_data['id'] = clinic.id
        if "clinic_uid" not in clinic_data:
            clinic_data["clinic_uid"] = clinic.id
        return jsonify(clinic_data)
    else:
        return make_response(jsonify({
            "message": f"No se encontró la clínica '{clinic_uuid}' para el cliente."
        }), 404)


def get_all_clients_with_clinics():
    """
    Get All Clients with Clinics
    ---
    tags:
      - Clinics
    responses:
      200:
        description: List of clients with clinics
      404:
        description: No clients found
    """
    clients = Client.query.all()

    if not clients:
        return make_response(jsonify({"message": "No se encontraron clientes."}), 404)

    full_data = []
    for client in clients:
        client_data = client.to_dict()
        client_data["id"] = client.id

        # Get clinics for this client
        clinics = Clinic.query.filter_by(client_id=client.id).all()
        clinic_list = []
        for clinic in clinics:
            clinic_data = clinic.to_dict()
            clinic_data["id"] = clinic.id
            clinic_list.append(clinic_data)

        client_data["clinics"] = clinic_list
        full_data.append(client_data)

    return jsonify(full_data)


def get_task_by_clinic_id(client_uuid, clinic_uuid):
    """
    Get Task by Clinic
    ---
    tags:
      - Tasks
    parameters:
      - in: path
        name: client_uuid
        type: string
        required: true
      - in: path
        name: clinic_uuid
        type: string
        required: true
    responses:
      200:
        description: Task details
      404:
        description: Task not found
    """
    task = Task.query.filter_by(
        client_id=client_uuid,
        clinic_id=clinic_uuid
    ).first()

    if task:
        task_data = task.to_dict()
        task_data['task_id'] = task.id
        return jsonify(task_data)

    return make_response(jsonify({"message": "Tareas no encontradas."}), 404)
