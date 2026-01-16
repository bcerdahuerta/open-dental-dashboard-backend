from datetime import datetime
import uuid
from flask import jsonify, request
from marshmallow import ValidationError
from extensions import db
from models import Task
from ...schemas.task_schema import TaskSchema


def create_task_controller(client_uuid: str, clinic_uuid: str):
    """
    Create a new Verification Task
    ---
    tags:
      - Tasks
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
      - name: body
        in: body
        required: true
        schema:
          id: Task
          required:
            - task_type
            - dates
          properties:
            task_type:
              type: string
              enum: ['new_day', 'corrective']
              description: Type of verification task
            dates:
              type: array
              description: List of dates for the task
              items:
                type: object
                properties:
                  date:
                    type: string
                    format: date
            priority:
              type: integer
              description: Task priority level
              default: 0
            status:
              type: string
              description: Initial task status
              default: pending
    responses:
      201:
        description: Task created successfully
        schema:
          type: object
          properties:
            message:
              type: string
            task_id:
              type: string
            data:
              type: object
      400:
        description: No data provided
      422:
        description: Validation error
      500:
        description: Internal server error
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No se proporcionaron datos para crear la tarea"}), 400

    data_for_validation = json_data.copy()
    data_for_validation['client_id'] = client_uuid
    data_for_validation['clinic_id'] = clinic_uuid

    try:
        validated_data = TaskSchema().load(data_for_validation)
        
        task_id = str(uuid.uuid4())
        
        new_task = Task(
            id=task_id,
            client_id=client_uuid,
            clinic_id=clinic_uuid,
            task_type=validated_data.get('task_type'),
            status=validated_data.get('status', 'pending'),
            priority=validated_data.get('priority', 0),
            dates=validated_data.get('dates'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_task)
        db.session.commit()

        return jsonify({
            "message": "Tarea creada exitosamente",
            "task_id": task_id,
            "data": new_task.to_dict()
        }), 201

    except ValidationError as err:
        return jsonify(err.messages), 422

    except Exception as e:
        db.session.rollback()
        print(f"Error al crear la tarea: {e}")
        return jsonify({"message": "Error interno del servidor al crear la tarea"}), 500


def patch_task_controller(client_uuid: str, clinic_uuid: str, task_id: str):
    """
    Update Task
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
      - in: path
        name: task_id
        type: string
        required: true
      - in: body
        name: body
        schema:
          type: object
    responses:
      200:
        description: Task updated
      400:
        description: Bad request
      403:
        description: Task status not pending
      404:
        description: Task not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No se proporcionaron datos para actualizar"}), 400

    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"message": "Tarea no encontrada"}), 404

        if task.client_id != client_uuid or task.clinic_id != clinic_uuid:
            return jsonify({"message": "La tarea no pertenece a la ruta de cliente/clínica especificada."}), 404

        if task.status != 'pending':
            return jsonify({"message": f"Solo se pueden actualizar tareas con status 'pending'. Status actual: {task.status}."}), 403

    except Exception as e:
        print(f"Error al verificar la tarea: {e}")
        return jsonify({"message": "Error interno del servidor al verificar la tarea"}), 500

    try:
        validated_data = TaskSchema(partial=True).load(json_data)
        fields_to_exclude = {
            'client_id',
            'clinic_id',
            'id',             
            'status',         
            'task_id',        
            'task_type'      
        }
        update_payload = {
            k: validated_data[k]
            for k in json_data.keys()
            if k in validated_data and k not in fields_to_exclude
        }

        if not update_payload:
            return jsonify({"message": "No se encontraron campos válidos para la actualización."}), 400

    except ValidationError as err:
        return jsonify({"validation_errors": err.messages}), 422
    except Exception as e:
        print(f"Error al validar los datos: {e}")
        return jsonify({"message": "La data no pudo ser validada."}), 422

    try:
        # Update fields dynamically
        for key, value in update_payload.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            "message": f"Tarea {task_id} actualizada exitosamente",
            "data": task.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar la tarea: {e}")
        return jsonify({"message": "Error interno del servidor al aplicar la actualización"}), 500


def delete_task_controller(client_uuid: str, clinic_uuid: str, task_id: str):
    """
    Delete Task
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
      - in: path
        name: task_id
        type: string
        required: true
    responses:
      204:
        description: Task deleted
      403:
        description: Task status not pending
      404:
        description: Task not found
    """
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({"message": "Tarea no encontrada"}), 404

        if task.client_id != client_uuid or task.clinic_id != clinic_uuid:
            return jsonify({"message": "La tarea no pertenece a la ruta de cliente/clínica especificada."}), 404

        if task.status != 'pending':
            return jsonify({
                "message": f"Solo se pueden eliminar tareas con status 'pending'. Status actual: {task.status}."
            }), 403 

        db.session.delete(task)
        db.session.commit()
        
        return "", 204

    except Exception as e:
        db.session.rollback()
        print(f"Error al eliminar la tarea: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar la tarea"}), 500
