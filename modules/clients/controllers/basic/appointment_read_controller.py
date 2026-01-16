from flask import jsonify, make_response, request
from datetime import datetime
from collections import defaultdict
from sqlalchemy import func
from extensions import db
from models import Appointment, Patient, Clinic


def get_appointment_report_by_practice(client_uuid, clinic_uuid):
    """
    Get Appointment Summary Report by Practice
    ---
    tags:
      - Appointments
    parameters:
      - name: client_uuid
        in: path
        type: string
        required: true
        description: UUID of the client
      - name: clinic_uuid
        in: path
        type: string
        required: true
        description: UUID of the clinic
      - name: date
        in: query
        type: string
        format: date
        required: true
        description: Date filter in YYYY-MM-DD format
    responses:
      200:
        description: Appointment summary report
        schema:
          type: object
          properties:
            total_appointments:
              type: integer
              description: Total number of appointments
            practices:
              type: object
              description: Breakdown by practice
              additionalProperties:
                type: object
                properties:
                  total:
                    type: integer
                  status_by_practice:
                    type: object
                    properties:
                      insurance_verification_status:
                        type: object
                      verification_type:
                        type: object
                      insurance_verification_process_result:
                        type: object
                  update_status_by_practice:
                    type: object
                    properties:
                      update_status:
                        type: object
                      upload_status:
                        type: object
      400:
        description: Missing or invalid date parameter
    """
    date_param = request.args.get('date')
    
    if not date_param:
        return make_response(jsonify({
            "message": "El parámetro 'date' es requerido para esta consulta. Formato: YYYY-MM-DD"
        }), 400)

    try:
        datetime.strptime(date_param, '%Y-%m-%d').date()
    except ValueError:
        return make_response(jsonify({
            "message": "Formato de fecha inválido. Por favor, usa el formato YYYY-MM-DD."
        }), 400)

    # SQLAlchemy Aggregation
    results = db.session.query(
        Appointment.practice,
        Appointment.verification_status,
        Appointment.process_result,
        Appointment.verification_type,
        Appointment.upload_status,
        Appointment.update_status,
        func.count(Appointment.id)
    ).filter(
        Appointment.clinic_id == clinic_uuid,
        Appointment.sheet_date == date_param
    ).group_by(
        Appointment.practice,
        Appointment.verification_status,
        Appointment.process_result,
        Appointment.verification_type,
        Appointment.upload_status,
        Appointment.update_status
    ).all()

    # Transformation (Map SQL results to the expected JSON structure)
    report = {
        "total_appointments": 0,
        "practices": defaultdict(lambda: {
            "total": 0,
            "status_by_practice": {
                "insurance_verification_status": defaultdict(int),
                "verification_type": defaultdict(int),
                "insurance_verification_process_result": defaultdict(int)
            },
            "update_status_by_practice": {
                "update_status": defaultdict(int),
                "upload_status": defaultdict(int),
            }
        })
    }

    for row in results:
        practice, v_status, p_result, v_type, up_status, upd_status, count = row
        # Ensure practice key is a string for JSON compliance
        practice_key = practice or "Unknown Practice"
        
        report["total_appointments"] += count
        report["practices"][practice_key]["total"] += count
        report["practices"][practice_key]["status_by_practice"]["insurance_verification_status"][v_status or "pending"] += count
        report["practices"][practice_key]["status_by_practice"]["verification_type"][v_type or "pending"] += count
        report["practices"][practice_key]["status_by_practice"]["insurance_verification_process_result"][p_result or "pending"] += count
        report["practices"][practice_key]["update_status_by_practice"]["upload_status"][up_status or "pending"] += count
        report["practices"][practice_key]["update_status_by_practice"]["update_status"][upd_status or "pending"] += count

    return jsonify(report)


def get_appointments_by_clinic_id(client_uuid, clinic_uuid):
    """
    Get Appointments by Clinic
    ---
    tags:
      - Appointments
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
        description: List of appointments
      404:
        description: Clinic not found
    """
    appointments = Appointment.query.filter_by(clinic_id=clinic_uuid).all()
    # Serialize to list of dicts
    return jsonify([appt.to_dict() for appt in appointments])
