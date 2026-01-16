from datetime import datetime
import uuid
from flask import jsonify, make_response, request
from marshmallow import ValidationError
from extensions import db
from models import Client, Clinic
from ...schemas.client_schema import ClientSchema
from integrations.ccc_integration import CCCIntegration


def create_client_controller():
    """
    Create a new Client
    ---
    tags:
      - Clients
    parameters:
      - name: body
        in: body
        required: true
        schema:
          id: Client
          required:
            - client_name
          properties:
            client_name:
              type: string
              description: Name of the client
            active:
              type: boolean
              description: Whether the client is active
              default: false
            ccc_username:
              type: string
              description: CCC integration username
            ccc_password:
              type: string
              description: CCC integration password
            clinics:
              type: array
              description: Optional list of clinics to create with the client
              items:
                type: object
                properties:
                  clinic_name:
                    type: string
                  spreadsheet_id:
                    type: string
                  folder_id:
                    type: string
                  ccc_id:
                    type: string
            CCC_enabled:
              type: object
              description: CCC integration settings
              properties:
                active:
                  type: boolean
                username:
                  type: string
                password:
                  type: string
    responses:
      201:
        description: Client created successfully
        schema:
          type: object
          properties:
            client_uid:
              type: string
            client_name:
              type: string
            message:
              type: string
      400:
        description: No data provided
      422:
        description: Validation error
      500:
        description: Internal server error
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No data provided"}), 400

    try:
        validated_data = ClientSchema().load(json_data)
        initial_clinic_data = validated_data.get('clinics', [])
        ccc_data = validated_data.get('CCC_enabled')
        
        # Extract client-specific fields
        client_data_for_db = {
            k: v for k, v in validated_data.items()
            if k not in ['clinics', 'CCC_enabled', 'gdrive_enabled', 'gsheet_enabled']
        }
    except ValidationError as client_err:
        return jsonify({"validation_errors": client_err.messages}), 422

    if validated_data is None:
        return jsonify({"error": "Data could not be validated against any known schema."}), 422

    try:
        # Create the client
        client_uid = str(uuid.uuid4())
        
        new_client = Client(
            id=client_uid,
            client_name=client_data_for_db.get('client_name'),
            active=client_data_for_db.get('active', False),
            ccc_username=client_data_for_db.get('ccc_username'),
            ccc_password=client_data_for_db.get('ccc_password'),
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_client)

        # Create clinics if provided
        if initial_clinic_data:
            clinics_to_process = initial_clinic_data if isinstance(
                initial_clinic_data, list) else [initial_clinic_data]
            
            for clinic_data in clinics_to_process:
                clinic_id = str(uuid.uuid4())
                new_clinic = Clinic(
                    id=clinic_id,
                    client_id=client_uid,
                    clinic_name=clinic_data.get('clinic_name'),
                    spreadsheet_id=clinic_data.get('spreadsheet_id'),
                    folder_id=clinic_data.get('folder_id'),
                    ccc_id=clinic_data.get('ccc_id')
                )
                db.session.add(new_clinic)

        db.session.commit()

        # Handle CCC integration if enabled
        if ccc_data and ccc_data.get("active") is True:
            username = ccc_data.get("username")
            password = ccc_data.get("password")

            ccc = CCCIntegration(username, password)
            token = ccc.authenticate()

            if token:
                ccc_response = ccc.create_client(validated_data.get("client_name"))
                print("Cliente creado en CCC:", ccc_response)

                if ccc_response:
                    ccc_clinic_id = ccc_response.get('clinicId')
                    # Update client with CCC metadata - would need to handle this differently
                    # For now, we can store in a separate field if needed

        return jsonify({
            "client_uid": client_uid,
            "client_name": new_client.client_name,
            "message": "Cliente creado exitosamente"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal Server Error: {e}", "message": "Failed to create client"}), 500


def update_client_partial_controller(client_uid):
    """
    Update Client
    ---
    tags:
      - Clients
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            client_name:
              type: string
            active:
              type: boolean
    responses:
      200:
        description: Client updated
      404:
        description: Client not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No se proporcionaron datos para la actualización parcial."}), 400

    try:
        validated_data = ClientSchema().load(json_data, partial=True)
        fields_to_exclude = {'client_uid', 'created_at', 'id'}
        
        client_data_to_update = {
            k: validated_data[k]
            for k in json_data.keys()
            if k in validated_data and k not in fields_to_exclude
        }

        if not client_data_to_update:
            return jsonify({"error": "No se encontraron campos válidos para la actualización."}), 400

    except ValidationError as err:
        return jsonify({"validation_errors": err.messages}), 422
    except Exception:
        return jsonify({"error": "La data no pudo ser validada."}), 422

    try:
        client = Client.query.get(client_uid)
        if not client:
            return jsonify({"error": f"Cliente con UID '{client_uid}' no encontrado."}), 404

        # Update fields dynamically
        for key, value in client_data_to_update.items():
            if hasattr(client, key):
                setattr(client, key, value)

        db.session.commit()

        return jsonify(client.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error del servicio al aplicar el PATCH: {str(e)}"}), 500


def delete_client_controller(client_uid):
    """
    Delete Client
    ---
    tags:
      - Clients
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
    responses:
      204:
        description: Client deleted
      404:
        description: Client not found
    """
    try:
        client = Client.query.get(client_uid)
        if not client:
            return jsonify({"error": f"Cliente con UID '{client_uid}' no encontrado."}), 404

        db.session.delete(client)
        db.session.commit()

        return "", 204

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error del servicio al eliminar el cliente: {str(e)}"}), 500
