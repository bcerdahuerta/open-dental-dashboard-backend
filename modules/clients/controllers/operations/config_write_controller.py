from flask import jsonify, request
from marshmallow import ValidationError
from ...schemas.config_schema import ConfigsSchema
from ...services.services import ConfigService


def create_config_controller(client_uuid, clinic_uuid, config_name):
    """
    Create Config
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
      - in: body
        name: body
        schema:
          type: object
          required:
            - yaml_content
    responses:
      201:
        description: Config created
      400:
        description: Validation error
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No se proporcionaron datos"}), 400

    try:
        validated_data = ConfigsSchema().load(json_data)
        
        config = ConfigService.create_or_update_config(
            client_uid=client_uuid,
            clinic_uid=clinic_uuid,
            config_name=config_name,
            yaml_content=validated_data.get('yaml_content')
        )

        return jsonify({"id": config['id'], "message": "Configuración creada exitosamente"}), 201

    except ValidationError as err:
        return jsonify({"errors": err.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def patch_config_controller(client_uuid, clinic_uuid, config_name, config_id):
    """
    Update Config
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
      - in: path
        name: config_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
    responses:
      200:
        description: Config updated
      400:
        description: Validation error
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400

    try:
        validated_data = ConfigsSchema().load(json_data, partial=True)
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422
    except Exception:
        return jsonify({"error": "La data no pudo ser validada."}), 400

    try:
        # Note: The service methods use (client_uid, clinic_uid, config_name) to identify the config.
        # But here we have a config_id. I'll use create_or_update logic if config_name is known,
        # or I can add an update_config_by_id to ConfigService if needed.
        # However, create_or_update_config matches the 'Upsert' nature of configs often used.
        # Given the task description, I'll use the service as implemented.
        
        config = ConfigService.create_or_update_config(
            client_uid=client_uuid,
            clinic_uid=clinic_uuid,
            config_name=config_name,
            yaml_content=validated_data.get('yaml_content')
        )

        return jsonify({
            "id": config['id'], 
            "message": "Configuración actualizada exitosamente", 
            "data": config
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

