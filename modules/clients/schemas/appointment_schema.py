from datetime import date, datetime
from marshmallow import Schema, fields, post_load
from marshmallow.validate import Length, Range, OneOf
from marshmallow import ValidationError


class AppointmentSchema(Schema):
    def __init__(self, client_uid=None, clinic_uid=None, **kwargs):
        super().__init__(**kwargs)

        # hay que almacenar los uid en self.context para que post_load pueda acceder a ellos
        if not hasattr(self, 'context'):
            self.context = {}
        self.context['client_uid'] = client_uid
        self.context['clinic_uid'] = clinic_uid

    # --- CAMPOS REQUERIDOS ---
    # UUIDs - Mejor validación
    appointment_id = fields.String(dump_only=True)
    client_uid = fields.UUID(dump_only=True)
    clinic_uid = fields.UUID(dump_only=True)

    # DATETIME fields
    appointment_datetime = fields.DateTime(format="iso", required=True)
    extraction_datetime = fields.DateTime(format="iso", required=True)
    created_at = fields.DateTime(load_default=datetime.now)

    # DATE fields (fechas de nacimiento/hoja)
    subscriber_dob = fields.Date(format="%Y-%m-%d", required=True)
    patient_dob = fields.Date(format="%Y-%m-%d", required=True)
    sheet_date = fields.Date(format="%Y-%m-%d", required=True)

    # Integer
    spreadsheet_row = fields.Integer(required=True)

    # String fields (Requeridos)
    practice = fields.String(required=True)
    carrier_name = fields.String(required=True)
    member_id = fields.String(required=True)
    subscriber_zip_code = fields.String(required=True)
    subscriber_first_name = fields.String(required=True)
    subscriber_last_name = fields.String(required=True)
    patient_first_name = fields.String(required=True)
    patient_last_name = fields.String(required=True)
    relationship_to_subscriber = fields.String(required=True)
    insurance_verification_process_result = fields.String(required=True)
    insurance_verification_status = fields.String(required=True)
    verification_type = fields.String(required=True)
    patnum = fields.String(required=True)
    plannum = fields.String(required=True)
    subscriber_patnum = fields.String(required=True)
    upload_status = fields.String(required=True)
    ordinal = fields.String(required=True)

    # --- CAMPOS OPCIONALES (con load_default) ---

    appointment_note = fields.String(allow_none=True, load_default="Empty")
    file_url = fields.String(allow_none=True, load_default="Empty")
    dr_comment = fields.String(allow_none=True, load_default="Empty")
    short_form_bks = fields.String(allow_none=True, load_default="Empty")
    plan_type = fields.String(allow_none=True, load_default="Empty")
    group_number = fields.String(allow_none=True, load_default="Empty")
    update_status = fields.String(allow_none=True, load_default="Empty")
    file_name = fields.String(allow_none=True, load_default="Empty")

    # DateTime Opcionales
    benefits_last_verified = fields.DateTime(format="iso", allow_none=True, load_default="Empty")
    elegibility_last_verified = fields.DateTime(format="iso", allow_none=True, load_default="Empty")

    # Dict Opcional
    custom_fields = fields.Dict(allow_none=True, load_default=dict)

    @post_load
    def make_appointment(self, data, **kwargs):
        # verificar que los datos necesarios del contexto existan
        context = self.context

        # 3. validacion de contexto
        if not context.get('client_uid') or not context.get('clinic_uid'):
            raise ValidationError("Client and Clinic UIDs must be provided during schema initialization.")

        # 4. hay que asignar campos externos debido al contexto
        data['client_uid'] = context['client_uid']
        data['clinic_uid'] = context['clinic_uid']
    
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = str(data['created_at'])

        ALL_DATE_TIME_FIELDS = [
            'subscriber_dob', 'patient_dob', 'sheet_date',
            'appointment_datetime', 'extraction_datetime',
            'benefits_last_verified', 'elegibility_last_verified'
        ]

        data.update({
            key: value.isoformat()
            for key, value in data.items()
            if key in ALL_DATE_TIME_FIELDS and (isinstance(value, (datetime, date)))
        })
                
        return data
