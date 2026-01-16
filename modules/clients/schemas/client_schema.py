from marshmallow import Schema, fields, post_load
from marshmallow.validate import Length
from datetime import datetime
import uuid
from .clinic_schema import ClinicSchema  # Importa el esquema de Clinic

class CCCEnabledSchema(Schema):
    active = fields.Boolean(required=True)
    username = fields.String(required=True, validate=Length(min=1))
    password = fields.String(required=True, validate=Length(min=1))

class ClientSchema(Schema):
    id = fields.String(dump_only=True)
    client_uid = fields.UUID(load_default=uuid.uuid4)
    client_name = fields.String(required=True, validate=Length(min=1))
    active = fields.Boolean(load_default=False)
    created_at = fields.DateTime(load_default=datetime.now)
    other_metadata = fields.Dict(required=False, allow_none=True, load_default={})
    clinics = fields.List(fields.Nested(ClinicSchema), required=False)

    # OPTIONAL
    CCC_enabled = fields.Nested(CCCEnabledSchema, required=False)
    gdrive_enabled = fields.Boolean(load_default=False)
    gsheet_enabled = fields.Boolean(load_default=False)

    @post_load
    def convert_types_to_string(self, data, **kwargs):
        # Convierte el UUID a cadena
        if 'client_uid' in data and isinstance(data['client_uid'], uuid.UUID):
            data['client_uid'] = str(data['client_uid'])

        # Convierte el datetime a cadena
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = str(data['created_at'])

        if "other_metadata" not in data or data["other_metadata"] is None:
            data["other_metadata"] = {}

        return data
