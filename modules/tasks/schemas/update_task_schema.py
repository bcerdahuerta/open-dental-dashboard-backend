from marshmallow import Schema, fields, validate

class UpdateTaskSchema(Schema):
    """
    Schema para validar actualizaciones parciales de una tarea.
    Ningún campo es obligatorio.
    """
    status = fields.String(
        required=True,
        validate=validate.OneOf(["in_progress", "completed", "failed"]),
        error_messages={"invalid": "El estado debe ser 'in_progress', 'completed' o 'failed'."}
    )
