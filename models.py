from extensions import db
from sqlalchemy import UniqueConstraint
from datetime import datetime, date

class Client(db.Model):
    __tablename__ = 'client'
    
    id = db.Column(db.String(36), primary_key=True)
    client_name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=False)
    ccc_username = db.Column(db.String(255))
    ccc_password = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    clinics = db.relationship('Clinic', backref='client', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'client_uid': self.id,
            'client_name': self.client_name,
            'active': self.active,
            'ccc_username': self.ccc_username,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Clinic(db.Model):
    __tablename__ = 'clinic'
    
    id = db.Column(db.String(36), primary_key=True)
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'), nullable=False)
    clinic_name = db.Column(db.String(255))
    spreadsheet_id = db.Column(db.String(255))
    folder_id = db.Column(db.String(255))
    ccc_id = db.Column(db.String(255))
    
    # Relationships
    appointments = db.relationship('Appointment', backref='clinic', lazy=True)
    patients = db.relationship('Patient', backref='clinic', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clinic_uid': self.id,
            'client_id': self.client_id,
            'clinic_name': self.clinic_name,
            'spreadsheet_id': self.spreadsheet_id,
            'folder_id': self.folder_id,
            'ccc_id': self.ccc_id
        }

class Patient(db.Model):
    __tablename__ = 'patient'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pat_num = db.Column(db.String(50), index=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    dob = db.Column(db.Date)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinic.id'), nullable=False)
    
    # Relationships
    appointments = db.relationship('Appointment', backref='patient', lazy=True)
    
    __table_args__ = (
        UniqueConstraint('pat_num', 'clinic_id', name='_pat_clinic_uc'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'pat_num': self.pat_num,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'dob': self.dob.isoformat() if self.dob else None,
            'clinic_id': self.clinic_id
        }

class Appointment(db.Model):
    __tablename__ = 'appointment'
    
    id = db.Column(db.String(36), primary_key=True)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinic.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    appointment_datetime = db.Column(db.DateTime)
    sheet_date = db.Column(db.Date)
    spreadsheet_row = db.Column(db.Integer)
    practice = db.Column(db.String(255))
    
    # Verification Data
    carrier_name = db.Column(db.String(255))
    verification_status = db.Column(db.String(100)) # Field: insurance_verification_status
    verification_type = db.Column(db.String(100))
    process_result = db.Column(db.String(255))    # Field: insurance_verification_process_result
    upload_status = db.Column(db.String(100))
    update_status = db.Column(db.String(100))
    
    # Raw Data
    raw_data = db.Column(db.JSON) # Stores short_form_bks, custom_fields, other_metadata

    def to_dict(self):
        data = {
            'id': self.id,
            'appointment_id': self.id,
            'clinic_id': self.clinic_id,
            'patient_id': self.patient_id,
            'appointment_datetime': self.appointment_datetime.isoformat() if self.appointment_datetime else None,
            'sheet_date': self.sheet_date.isoformat() if self.sheet_date else None,
            'spreadsheet_row': self.spreadsheet_row,
            'practice': self.practice,
            'carrier_name': self.carrier_name,
            'insurance_verification_status': self.verification_status,
            'verification_type': self.verification_type,
            'insurance_verification_process_result': self.process_result,
            'upload_status': self.upload_status,
            'update_status': self.update_status
        }
        if self.raw_data:
            data.update(self.raw_data)
        return data


class ClientConfig(db.Model):
    __tablename__ = 'client_config'
    
    id = db.Column(db.String(36), primary_key=True)
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'), nullable=False)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinic.id'), nullable=True)
    config_name = db.Column(db.String(100), nullable=False)
    yaml_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'clinic_id': self.clinic_id,
            'config_name': self.config_name,
            'yaml_content': self.yaml_content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Task(db.Model):
    __tablename__ = 'task'
    
    id = db.Column(db.String(36), primary_key=True)
    client_id = db.Column(db.String(36), db.ForeignKey('client.id'), nullable=False)
    clinic_id = db.Column(db.String(36), db.ForeignKey('clinic.id'), nullable=False)
    task_type = db.Column(db.String(50), nullable=False)  # 'new_day', 'corrective', 'in_advanced'
    status = db.Column(db.String(50), default='pending')  # 'pending', 'in_progress', 'completed', 'failed'
    priority = db.Column(db.Integer, default=0)
    dates = db.Column(db.JSON)  # Stores list: [{'date': '2025-10-02'}]
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.id,
            'client_id': self.client_id,
            'clinic_id': self.clinic_id,
            'task_type': self.task_type,
            'status': self.status,
            'priority': self.priority,
            'dates': self.dates,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
