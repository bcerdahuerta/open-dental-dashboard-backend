from flask import Response, jsonify, make_response, request
from models import Client, ClientConfig


def get_config_by_client_id_and_config_name(client_uuid, clinic_uuid, config_name):
    """
    Get Config Content
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
    if client_uuid and config_name:
        config = ClientConfig.query.filter_by(
            client_id=client_uuid,
            clinic_id=clinic_uuid,
            config_name=config_name
        ).first()

        if config and config.yaml_content:
            return Response(config.yaml_content, mimetype='text/yaml')

    return Response("Configuración no encontrada", status=404)


def get_config_filenames_by_client_id(client_uid: str, clinic_uid: str) -> dict:
    """
    Get Config Filenames
    ---
    tags:
      - Configs
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
      - in: path
        name: clinic_uid
        type: string
        required: true
    responses:
      200:
        description: List of config files
      404:
        description: No configs found
    """
    if not client_uid:
        return make_response(jsonify({"message": "ID de cliente no proporcionado."}), 400)

    configs = ClientConfig.query.filter_by(
        client_id=client_uid,
        clinic_id=clinic_uid
    ).all()

    config_files_list = []
    for config in configs:
        if config.config_name:
            config_files_list.append({
                "name": config.config_name,
                "id": config.id
            })

    if config_files_list:
        return jsonify({
            "client_id": client_uid,
            "clinic_id": clinic_uid,
            "config_files": config_files_list,
            "count": len(config_files_list)
        })
    else:
        return make_response(jsonify({
            "message": f"No se encontraron configuraciones para el cliente {client_uid} y clínica {clinic_uid}."
        }), 404)


def get_client_by_document_id(client_uuid):
    """
    Get Client by ID
    ---
    tags:
      - Clients
    parameters:
      - in: path
        name: client_uuid
        type: string
        required: true
    responses:
      200:
        description: Client object
      404:
        description: Client not found
    """
    client = Client.query.get(client_uuid)
    if client:
        return jsonify(client.to_dict())

    return make_response(jsonify({"message": "Cliente no encontrado."}), 404)


def get_client_by_name(client_name):
    """
    Get a client by name.
    """
    client = Client.query.filter_by(client_name=client_name).first()
    if client:
        return jsonify(client.to_dict())

    return make_response(jsonify({"message": "Cliente no encontrado por nombre."}), 404)


def get_client_by_status(status):
    """
    Get clients filtered by active status.
    """
    status_bool = {'active': True, 'disabled': False}.get(status, None)

    if status_bool is None:
        return make_response(jsonify({"message": "Status no válido."}), 400)

    clients = Client.query.filter_by(active=status_bool).all()

    if not clients:
        return make_response(jsonify({"message": "Clientes no encontrados por estado."}), 404)

    clients_list = [c.to_dict() for c in clients]
    return jsonify(clients_list)


def get_all_clients():
    """
    Get All Clients
    ---
    tags:
      - Clients
    parameters:
      - in: query
        name: name
        type: string
        description: Filter by client name
      - in: query
        name: status
        type: string
        description: Filter by client status (active/disabled)
    responses:
      200:
        description: List of clients
      404:
        description: No clients found
    """
    client_name_param = request.args.get('name')
    client_status_param = request.args.get('status')

    if client_name_param:
        return get_client_by_name(client_name_param)

    if client_status_param:
        return get_client_by_status(client_status_param)

    clients = Client.query.all()

    if not clients:
        return make_response(jsonify({"message": "No se encontraron clientes."}), 404)

    clients_list = [c.to_dict() for c in clients]
    return jsonify(clients_list)

