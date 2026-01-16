from marshmallow import Schema, fields, validate


class ConfigsSchema(Schema):
    id = fields.String(dump_only=True)

    client_id = fields.String(
        required=True,
        validate=validate.Length(
            min=1, error="El client_id no puede estar vacío.")
    )

    clinic_id = fields.String(
        required=False,
        allow_none=True
    )

    config_name = fields.String(
        required=True,
        validate=validate.OneOf(
            ["settings", "ruleset"],
            error="La configuracion debe ser 'settings' o 'ruleset'."
        ),
        error_messages={"required": "El campo 'config_name' es obligatorio."}
    )

    yaml_content = fields.String(
        required=True,
        validate=validate.Length(
            min=1, error="El contenido YAML no puede estar vacío.")
    )

    created_at = fields.DateTime(dump_only=True)
