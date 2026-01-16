from datetime import date, datetime
from marshmallow import Schema, fields, post_load, validate


class DateObjectSchema(Schema):
    """
    Schema para validar cada objeto de fecha dentro del array 'dates'.
    """
    date = fields.Date(
        required=True,
        format="%Y-%m-%d",
        error_messages={"required": "El campo de fecha es obligatorio."}
    )

    @post_load
    def convert_date_to_string(self, data, **kwargs):
        date_obj = data.get('date')
        if isinstance(date_obj, (date, datetime)): 
            data['date'] = date_obj.strftime("%Y-%m-%d")
        return data


class TaskSchema(Schema):
    """
    Schema principal para validar el payload completo de la tarea.
    """
    client_id = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "El campo 'client_id' es obligatorio."}
    )
    clinic_id = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "El campo 'clinic_id' es obligatorio."}
    )
    task_type = fields.String(
        required=True,
        validate=validate.OneOf(
            ["new_day", "corrective", "in_advanced"],
            error="La tarea debe ser 'new_day', 'corrective' o 'in_advanced'."
        ),
        error_messages={"required": "El campo 'task' es obligatorio."}
    )
    dates = fields.List(
        fields.Nested(DateObjectSchema),
        required=True,
        validate=validate.Length(
            min=1, error="El array de fechas no puede estar vacío."),
        error_messages={"required": "El campo 'dates' es obligatorio."}
    )
    priority = fields.Integer(
        required=True,
        validate=validate.Range(
            min=1, max=5, error="La prioridad debe ser un número entre 1 y 5."),
        error_messages={"required": "El campo 'priority' es obligatorio."}
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(
            ["pending", "in_progress", "completed", "failed"],
            error="El status debe ser 'pending', 'in_progress' o 'completed'."
        ),
        load_default="pending",
    )

