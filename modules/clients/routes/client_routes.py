from . import clients_bp
from ..controllers.basic.client_read_controller import get_all_clients, get_client_by_document_id, get_config_by_client_id_and_config_name, get_config_filenames_by_client_id
from ..controllers.basic.clinic_read_controller import get_clinics_by_client_id, get_clinic_by_uuid_for_client, get_all_clients_with_clinics, get_config_by_clinic_id, get_task_by_clinic_id
from ..controllers.basic.appointment_read_controller import get_appointments_by_clinic_id, get_appointment_report_by_practice
from ..controllers.operations.client_write_controller import create_client_controller, delete_client_controller, update_client_partial_controller
from ..controllers.operations.clinic_write_controller import create_clinic_controller, delete_clinic_controller, update_clinic_partial_controller
from modules.clients.controllers.operations.appointment_write_controller import create_appointment_controller, delete_appointment_controller, update_appointment_controller
from ..controllers.operations.config_write_controller import create_config_controller, patch_config_controller
from ..controllers.operations.task_write_controller import create_task_controller, patch_task_controller, delete_task_controller

# ---------------
# GET /clients/clinics/appointments
# ---------------

clients_bp.add_url_rule(  # busqueda general de appointments soporta: summary?date=<YYYY-MM-DD>
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/appointments/summary",
    view_func=get_appointment_report_by_practice,
    methods=["GET"],
)

clients_bp.add_url_rule(  # busqueda general de appointments
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/appointments",
    view_func=get_appointments_by_clinic_id,
    methods=["GET"],
)

# ---------------
# POST|PATCH|DELETE /clients/clinics/appointments
# ---------------

clients_bp.add_url_rule(
    "/<string:client_uid>/clinics/<string:clinic_uid>/appointments",
    view_func=create_appointment_controller,
    methods=["POST"],
)

clients_bp.add_url_rule(
    "/<string:client_uid>/clinics/<string:clinic_uid>/appointments/<string:appointment_id>",
    view_func=update_appointment_controller,
    methods=["PATCH"]
)

clients_bp.add_url_rule(
    "/<string:client_uid>/clinics/<string:clinic_uid>/appointments/<string:appointment_id>",
    view_func=delete_appointment_controller,
    methods=["DELETE"]
)
# ---------------
# GET /clients/clinics/configs
# ---------------

clients_bp.add_url_rule(  # busqueda por client uuid, clinic uuid y config name <ruleset, settings>
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/configs/<string:config_name>",
    view_func=get_config_by_client_id_and_config_name,
    methods=["GET"],
)

clients_bp.add_url_rule(  # busqueda por client uuid, clinic uuid y config name <ruleset, settings>
    "/<string:client_uid>/clinics/<string:clinic_uid>/configs",
    view_func=get_config_filenames_by_client_id,
    methods=["GET"],
)

# ---------------
# GET /clients/clinics/tasks
# ---------------

clients_bp.add_url_rule(  # busqueda por client uuid y clinic uuid
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/tasks",
    view_func=get_task_by_clinic_id,
    methods=["GET"],
)

# ---------------
# GET /clients/clinics
# ---------------

clients_bp.add_url_rule(  # busqueda por client uuid y clinic uuid
    "/<string:client_uuid>/clinics/<string:clinic_uuid>",
    view_func=get_clinic_by_uuid_for_client,
    methods=["GET"],
)


clients_bp.add_url_rule(  # busqueda general de clinicas por uuid
    "/<string:client_uuid>/clinics",
    view_func=get_clinics_by_client_id,
    methods=["GET"],
)


clients_bp.add_url_rule(  # busqueda por todos los clientes y clinicas
    "/clinics",
    view_func=get_all_clients_with_clinics,
    methods=["GET"],
)

# ---------------
# POST|PATCH /clients/clinics/tasks
# ---------------

# CREACION Y MODIFICACION DE TAREAS
clients_bp.add_url_rule(  # Ejecuta nuevo dia por client uuid y clinic uuid
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/tasks",
    view_func=create_task_controller,
    methods=["POST"],
)

clients_bp.add_url_rule(  # Ejecuta nuevo dia por client uuid y clinic uuid
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/tasks/<string:task_id>",
    view_func=patch_task_controller,
    methods=["PATCH"],
)

clients_bp.add_url_rule(
    "/<string:client_uuid>/clinics/<string:clinic_uuid>/tasks/<string:task_id>",
    view_func=delete_task_controller,
    methods=["DELETE"],
)
# ---------------
# POST|PATCH /clients/clinics/configs/<config_name>
# ---------------

clients_bp.add_url_rule(
    "<string:client_uuid>/clinics/<string:clinic_uuid>/configs/<string:config_name>",
    view_func=create_config_controller,
    methods=["POST"],
)

clients_bp.add_url_rule(
    "<string:client_uuid>/clinics/<string:clinic_uuid>/configs/<string:config_name>/<string:config_id>",
    view_func=patch_config_controller,
    methods=["PATCH"],
)

# ---------------
# POST|PATCH|PUT|DELETE /clients/clinics/<clinic_uid>
# ---------------
clients_bp.add_url_rule(
    "/<string:client_uid>/clinics",
    view_func=create_clinic_controller,
    methods=["POST"],
)

clients_bp.add_url_rule(
    "/<string:client_uid>/clinics/<string:clinic_uid>",
    view_func=update_clinic_partial_controller,
    methods=["PATCH"],
)

clients_bp.add_url_rule(
    "/<string:client_uid>/clinics/<string:clinic_uid>",
    view_func=delete_clinic_controller,
    methods=["DELETE"],
)


# ---------------
# GET /clients
# ---------------

clients_bp.add_url_rule(  # permite la busqueda por uuid
    "/<string:client_uuid>",
    view_func=get_client_by_document_id,
    methods=["GET"],
)

clients_bp.add_url_rule(  # vista general  /clients o /clients?name=<name> o /client?status=<active/disabled>
    "/", view_func=get_all_clients, methods=["GET"]
)

# ---------------
# POST|PUT|PATCH|DELETE /clients
# ---------------

clients_bp.add_url_rule(
    "/",
    view_func=create_client_controller,
    methods=["POST"],
)

clients_bp.add_url_rule(
    "/<string:client_uid>",
    view_func=update_client_partial_controller,
    methods=["PATCH"],
)

clients_bp.add_url_rule(
    "/<string:client_uid>",
    view_func=delete_client_controller,
    methods=["DELETE"],
)
