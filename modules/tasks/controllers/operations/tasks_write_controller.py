from flask import jsonify, request
from marshmallow import ValidationError
from ...schemas.update_task_schema import UpdateTaskSchema
from ....clients.services.services import TaskService


def update_task_status(task_id):
    """
    Update Task Status
    ---
    tags:
      - Tasks
    parameters:
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
      404:
        description: Task not found
    """
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No hay datos para actualizar"}), 400

    try:
        validated_data = UpdateTaskSchema().load(json_data, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 422
    except Exception as e:
        return jsonify({"message": f"Error en la validación o procesamiento de datos: {str(e)}"}), 400 

    try:
        updated_task = TaskService.update_task_status(task_id, validated_data)
        if not updated_task:
            return jsonify({"message": "Tarea no encontrada"}), 404

        return jsonify({
            "message": f"Tarea {task_id} actualizada exitosamente",
            "data": updated_task
        }), 200

    except Exception as e:
        print(f"Error al actualizar la tarea: {e}")
        return jsonify({"message": "Error interno del servidor al actualizar la tarea"}), 500


def delete_task(task_id: str):
    """
    Delete Task
    ---
    tags:
      - Tasks
    parameters:
      - in: path
        name: task_id
        type: string
        required: true
    responses:
      204:
        description: Task deleted
      404:
        description: Task not found
    """
    try:
        success = TaskService.delete_task(task_id)
        if not success:
            return jsonify({"message": "Tarea no encontrada"}), 404

        return "", 204

    except Exception as e:
        print(f"Error al eliminar la tarea: {e}")
        return jsonify({"message": "Error interno del servidor al eliminar la tarea"}), 500

