from . import tasks_bp
from ..controllers.basic.tasks_read_controller import get_all_tasks
from ..controllers.operations.tasks_write_controller import delete_task, update_task_status
# ---------------
# GET /tasks
# ---------------

tasks_bp.add_url_rule("/", view_func=get_all_tasks, methods=["GET"])


# ---------------
# PATCH|DELETE /clients
# ---------------

tasks_bp.add_url_rule(
    "/<string:task_id>",
    view_func=update_task_status,
    methods=["PATCH"]
)

tasks_bp.add_url_rule(
    "/<string:task_id>",
    view_func=delete_task,
    methods=["DELETE"]
)
