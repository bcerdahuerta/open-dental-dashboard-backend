from flask import jsonify, make_response
from models import Task


def get_all_tasks():
    """
    Get All Tasks
    ---
    tags:
      - Tasks
    responses:
      200:
        description: List of tasks
      404:
        description: No tasks found
    """
    tasks = Task.query.all()

    if not tasks:
        return make_response(jsonify({"message": "No se encontraron tareas."}), 404)

    task_list = [task.to_dict() for task in tasks]
    return jsonify(task_list)
