from flask import jsonify, request
from marshmallow import ValidationError
from ...schemas.clinic_schema import ClinicSchema
from ...services.services import ClinicService, ClientService


def create_clinic_controller(client_uid: str):
    """
    Create Clinic(s)
    ---
    tags:
      - Clinics
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: array
          items:
             type: object
             required:
               - clinic_name
             properties:
               clinic_name:
                 type: string
               spreadsheet_id:
                 type: string
    responses:
      201:
        description: Created clinics
      400:
        description: Bad request
      404:
        description: Client not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Se requieren datos para la creación de la clínica(s)."}), 400

    if not isinstance(json_data, list):
        return jsonify({"error": "Se espera una lista de clínicas para esta operación."}), 400

    try:
        validated_data_list = ClinicSchema(many=True).load(json_data)
    except ValidationError as err:
        return jsonify({"validation_errors": err.messages}), 422
    except Exception as e:
        return jsonify({"error": f"La data no pudo ser validada. Causa: {str(e)}"}), 422

    try:
        # Verify client exists
        client = ClientService.get_client(client_uid)
        if not client:
            return jsonify({"error": f"Cliente con UID '{client_uid}' no encontrado."}), 404

        created_clinics = []
        for clinic_data in validated_data_list:
            created_clinic = ClinicService.create_clinic(client_uid, clinic_data)
            created_clinics.append(created_clinic)

        if not created_clinics:
            return jsonify({"error": "Error interno: no se pudo crear ninguna clínica."}), 500

        return jsonify(created_clinics), 201

    except Exception as e:
        return jsonify({"error": f"Error del servicio al crear la clínica(s): {str(e)}"}), 500


def update_clinic_partial_controller(client_uid: str, clinic_uid: str):
    """
    Update Clinic
    ---
    tags:
      - Clinics
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
      - in: path
        name: clinic_uid
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
    responses:
      200:
        description: Clinic updated
      404:
        description: Clinic not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No se proporcionaron datos para la actualización parcial."}), 400

    try:
        validated_data = ClinicSchema().load(json_data, partial=True)
    except ValidationError as err:
        return jsonify({"validation_errors": err.messages}), 422
    except Exception as e:
        return jsonify({"error": f"La data no pudo ser validada. Causa: {str(e)}"}), 422

    try:
        updated_clinic = ClinicService.update_clinic(client_uid, clinic_uid, validated_data)
        if not updated_clinic:
            return jsonify({"error": f"Clínica con UID '{clinic_uid}' no encontrada para el cliente '{client_uid}'."}), 404

        return jsonify(updated_clinic), 200

    except Exception as e:
        return jsonify({"error": f"Error del servicio al aplicar el PATCH: {str(e)}"}), 500


def delete_clinic_controller(client_uid: str, clinic_uid: str):
    """
    Delete Clinic
    ---
    tags:
      - Clinics
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
      204:
        description: Clinic deleted
      404:
        description: Clinic not found
    """
    try:
        success = ClinicService.delete_clinic(client_uid, clinic_uid)
        if not success:
            return jsonify({"error": f"Clínica con UID '{clinic_uid}' no encontrada."}), 404

        return "", 204

    except Exception as e:
        return jsonify({"error": f"Error del servicio al intentar eliminar la clínica: {str(e)}"}), 500

