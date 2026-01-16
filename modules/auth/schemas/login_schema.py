from marshmallow import Schema, fields

from marshmallow import Schema, fields, validate

class LoginSchema(Schema):
    """
    Schema para validar el cuerpo de la petición de login.
    """
    email = fields.String(
        required=True,
        validate=validate.Email(error="El campo 'email' no tiene un formato válido."),
        error_messages={"required": "El campo 'email' es obligatorio."}
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=6, error="La contraseña debe tener al menos 6 caracteres."),
        error_messages={"required": "El campo 'password' es obligatorio."}
    )
