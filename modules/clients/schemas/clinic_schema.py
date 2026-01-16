from datetime import datetime
import uuid
from marshmallow import Schema, fields, post_load  # type: ignore
from marshmallow.validate import Length  # type: ignore
from .appointment_schema import AppointmentSchema


class ClinicSchema(Schema):
    id = fields.String(dump_only=True)
    clinic_uid = fields.UUID(load_default=uuid.uuid4)
    clinic_name = fields.String(required=True, validate=Length(min=1))
    active = fields.Boolean(load_default=False)
    created_at = fields.DateTime(load_default=datetime.now)
    ccc_id = fields.String(required=False, allow_none=True)
    spreadsheet_id = fields.String(required=False, allow_none=True)
    folder_id = fields.String(required=False, allow_none=True)
    other_metadata = fields.Dict(required=False, load_default={})

    @post_load
    def make_clinic(self, data, **kwargs):
        if "ccc_id" not in data or data["ccc_id"] is None:
            data["ccc_id"] = None
        if "spreadsheet_id" not in data or data["spreadsheet_id"] is None:
            data["spreadsheet_id"] = None
        if "folder_id" not in data or data["folder_id"] is None:
            data["folder_id"] = None

        if 'clinic_uid' in data and isinstance(data['clinic_uid'], uuid.UUID):
            data['clinic_uid'] = str(data['clinic_uid'])

        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = str(data['created_at'])

        if "other_metadata" not in data or data["other_metadata"] is None:
            data["other_metadata"] = {}
        return data
