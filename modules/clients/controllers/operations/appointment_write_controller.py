from datetime import datetime
import uuid
from flask import jsonify, request
from marshmallow import ValidationError
from extensions import db
from models import Client, Clinic, Appointment, Patient
from ...schemas.appointment_schema import AppointmentSchema


def create_appointment_controller(client_uid: str, clinic_uid: str):
    """
    Create Appointment(s)
    ---
    tags:
      - Appointments
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
          type: array
          items:
             type: object
             required:
               - sheet_date
             properties:
               sheet_date:
                 type: string
                 format: date
               practice:
                 type: string
    responses:
      201:
        description: Created appointments
      400:
        description: Bad request
      404:
        description: Clinic not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "Se requieren datos para la creación de un appointment."}), 400

    if not isinstance(json_data, list):
        return jsonify({"error": "Se espera una lista de appointments para esta operación."}), 400

    schema = AppointmentSchema(client_uid=client_uid, clinic_uid=clinic_uid)

    try:
        validated_data_list = schema.load(json_data, many=True)
    except ValidationError as err:
        return jsonify({"validation_errors": err.messages}), 422
    except Exception as e:
        return jsonify({"error": f"La data no pudo ser validada. Causa: {str(e)}"}), 422

    try:
        # Verify client and clinic exist
        client = Client.query.get(client_uid)
        if not client:
            return jsonify({"error": f"Cliente con UID '{client_uid}' no encontrado."}), 404

        clinic = Clinic.query.filter_by(id=clinic_uid, client_id=client_uid).first()
        if not clinic:
            return jsonify({"error": f"Clínica con UID '{clinic_uid}' no encontrada."}), 404

        created_appointments = []
        for appointment_data in validated_data_list:
            appointment_id = str(uuid.uuid4())
            
            # Get or create patient
            patient_id = appointment_data.get('patient_id')
            if not patient_id:
                # If patient data is embedded, create patient first
                pat_num = appointment_data.get('pat_num')
                if pat_num:
                    patient = Patient.query.filter_by(pat_num=pat_num, clinic_id=clinic_uid).first()
                    if not patient:
                        patient = Patient(
                            pat_num=pat_num,
                            first_name=appointment_data.get('first_name'),
                            last_name=appointment_data.get('last_name'),
                            clinic_id=clinic_uid
                        )
                        db.session.add(patient)
                        db.session.flush()  # Get the ID
                    patient_id = patient.id

            new_appointment = Appointment(
                id=appointment_id,
                clinic_id=clinic_uid,
                patient_id=patient_id,
                appointment_datetime=appointment_data.get('appointment_datetime'),
                sheet_date=appointment_data.get('sheet_date'),
                spreadsheet_row=appointment_data.get('spreadsheet_row'),
                practice=appointment_data.get('practice'),
                carrier_name=appointment_data.get('carrier_name'),
                verification_status=appointment_data.get('insurance_verification_status'),
                verification_type=appointment_data.get('verification_type'),
                process_result=appointment_data.get('insurance_verification_process_result'),
                upload_status=appointment_data.get('upload_status'),
                raw_data=appointment_data.get('raw_data')
            )
            
            db.session.add(new_appointment)
            created_appointments.append(appointment_id)

        db.session.commit()

        if not created_appointments:
            return jsonify({"error": "Error interno: no se pudo crear ningun appointment."}), 500

        return jsonify({
            "message": f"Creado exitosamente, {len(created_appointments)} appointments",
            "count": len(created_appointments)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error del servicio al crear la clínica(s): {str(e)}"}), 500


def update_appointment_controller(client_uid: str, clinic_uid: str, appointment_id: str):
    """
    Update Appointment
    ---
    tags:
      - Appointments
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
      - in: path
        name: clinic_uid
        type: string
        required: true
      - in: path
        name: appointment_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
    responses:
      200:
        description: Appointment updated
      404:
        description: Appointment not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"error": "No se proporcionaron datos para la actualización."}), 400

    schema = AppointmentSchema(client_uid=client_uid, clinic_uid=clinic_uid)

    try:
        validated_data = schema.load(json_data, partial=True)

        fields_to_exclude = {
            'appointment_id',
            'created_at',
            'client_uid',
            'clinic_uid',
            'id'
        }

        appointment_data_to_update = {
            k: validated_data[k]
            for k in json_data.keys()
            if k in validated_data and k not in fields_to_exclude
        }

        if not appointment_data_to_update:
            return jsonify({"error": "No se encontraron campos válidos para la actualización."}), 400

    except ValidationError as err:
        return jsonify({"validation_errors": err.messages}), 422
    except Exception as e:
        return jsonify({"error": f"La data no pudo ser validada. Causa: {str(e)}"}), 422

    try:
        appointment = Appointment.query.filter_by(id=appointment_id, clinic_id=clinic_uid).first()
        if not appointment:
            return jsonify({"error": "Error interno al intentar actualizar el appointment, o el recurso no existe."}), 404

        # Map schema fields to model fields
        field_mapping = {
            'insurance_verification_status': 'verification_status',
            'insurance_verification_process_result': 'process_result'
        }

        # Update fields dynamically
        for key, value in appointment_data_to_update.items():
            model_key = field_mapping.get(key, key)
            if hasattr(appointment, model_key):
                setattr(appointment, model_key, value)

        db.session.commit()

        return jsonify(appointment.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error del servicio al intentar actualizar el appointment: {str(e)}"}), 500


def delete_appointment_controller(client_uid: str, clinic_uid: str, appointment_id: str):
    """
    Delete Appointment
    ---
    tags:
      - Appointments
    parameters:
      - in: path
        name: client_uid
        type: string
        required: true
      - in: path
        name: clinic_uid
        type: string
        required: true
      - in: path
        name: appointment_id
        type: string
        required: true
    responses:
      204:
        description: Appointment deleted
      404:
        description: Appointment not found
    """
    try:
        appointment = Appointment.query.filter_by(id=appointment_id, clinic_id=clinic_uid).first()
        if not appointment:
            return jsonify({"error": "Error interno al intentar eliminar el appointment."}), 404

        db.session.delete(appointment)
        db.session.commit()

        return "", 204

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error del servicio al intentar eliminar el appointment: {str(e)}"}), 500
