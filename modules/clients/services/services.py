"""
Service Layer for Client and Appointment operations.
Replaces the legacy DBManager wrapper with direct SQLAlchemy usage.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from extensions import db
from models import Client, Clinic, Patient, Appointment, Task, ClientConfig


class ClientService:
    """Service class for Client CRUD operations."""

    @staticmethod
    def create_client(client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new Client record.
        
        Args:
            client_data: Dictionary containing client fields.
            
        Returns:
            Dictionary representation of the created client.
        """
        data = client_data.copy()
        if 'id' not in data and 'client_uid' in data:
            data['id'] = data.pop('client_uid')
        elif 'id' not in data:
            data['id'] = str(uuid.uuid4())

        client = Client(**data)
        db.session.add(client)
        db.session.commit()
        return client.to_dict()

    @staticmethod
    def update_client(client_uid: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update an existing Client record.
        
        Args:
            client_uid: The client's unique identifier.
            updates: Dictionary of fields to update.
            
        Returns:
            Dictionary representation of the updated client, or None if not found.
        """
        client = Client.query.get(client_uid)
        if not client:
            return None
            
        for key, value in updates.items():
            if hasattr(client, key):
                setattr(client, key, value)
                
        db.session.commit()
        return client.to_dict()

    @staticmethod
    def get_client(client_uid: str) -> Optional[Dict[str, Any]]:
        """Get a client by ID."""
        client = Client.query.get(client_uid)
        return client.to_dict() if client else None

    @staticmethod
    def delete_client(client_uid: str) -> bool:
        """Delete a client by ID."""
        client = Client.query.get(client_uid)
        if not client:
            return False
        db.session.delete(client)
        db.session.commit()
        return True


class ClinicService:
    """Service class for Clinic CRUD operations."""

    @staticmethod
    def create_clinic(client_uid: str, clinic_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new clinic for a client."""
        clinic_id = clinic_data.get('id') or str(uuid.uuid4())
        
        new_clinic = Clinic(
            id=clinic_id,
            client_id=client_uid,
            clinic_name=clinic_data.get('clinic_name'),
            spreadsheet_id=clinic_data.get('spreadsheet_id'),
            folder_id=clinic_data.get('folder_id'),
            ccc_id=clinic_data.get('ccc_id')
        )
        
        db.session.add(new_clinic)
        db.session.commit()
        return new_clinic.to_dict()

    @staticmethod
    def update_clinic(client_uid: str, clinic_uid: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing clinic."""
        clinic = Clinic.query.filter_by(id=clinic_uid, client_id=client_uid).first()
        if not clinic:
            return None

        fields_to_exclude = {'clinic_uid', 'created_at', 'id', 'client_id'}
        for key, value in updates.items():
            if hasattr(clinic, key) and key not in fields_to_exclude:
                setattr(clinic, key, value)

        db.session.commit()
        return clinic.to_dict()

    @staticmethod
    def delete_clinic(client_uid: str, clinic_uid: str) -> bool:
        """Delete a clinic by ID."""
        clinic = Clinic.query.filter_by(id=clinic_uid, client_id=client_uid).first()
        if not clinic:
            return False
        
        db.session.delete(clinic)
        db.session.commit()
        return True


class AppointmentService:
    """Service class for Appointment CRUD operations."""

    @staticmethod
    def create_appointments_bulk(
        clinic_uid: str,
        appointments_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create multiple appointments in a single transaction using bulk insert.
        
        This method uses db.session.add_all() for significant performance gains
        over individual inserts when processing large batches.
        
        Args:
            clinic_uid: The clinic's unique identifier.
            appointments_data: List of appointment dictionaries.
            
        Returns:
            List of created appointment dictionaries.
        """
        appointments_to_add = []
        patients_to_add = []
        patient_cache = {}  # Cache for patients we create in this batch

        # First pass: identify and create any missing patients
        for appt_data in appointments_data:
            pat_num = appt_data.get('patnum') or appt_data.get('pat_num')
            if not pat_num:
                continue

            cache_key = f"{pat_num}:{clinic_uid}"
            if cache_key not in patient_cache:
                # Check if patient exists in DB
                patient = Patient.query.filter_by(pat_num=pat_num, clinic_id=clinic_uid).first()
                if not patient:
                    # Parse DOB if string
                    dob = appt_data.get('patient_dob')
                    if isinstance(dob, str):
                        try:
                            dob = datetime.strptime(dob, '%Y-%m-%d').date()
                        except ValueError:
                            dob = None

                    patient = Patient(
                        pat_num=pat_num,
                        clinic_id=clinic_uid,
                        first_name=appt_data.get('patient_first_name') or appt_data.get('first_name'),
                        last_name=appt_data.get('patient_last_name') or appt_data.get('last_name'),
                        dob=dob
                    )
                    patients_to_add.append(patient)
                patient_cache[cache_key] = patient

        # Bulk add patients and flush to get IDs
        if patients_to_add:
            db.session.add_all(patients_to_add)
            db.session.flush()

        # Second pass: create appointments
        for appt_data in appointments_data:
            pat_num = appt_data.get('patnum') or appt_data.get('pat_num')
            cache_key = f"{pat_num}:{clinic_uid}"
            patient = patient_cache.get(cache_key)

            if not patient:
                # Try to get from DB if not in cache
                patient = Patient.query.filter_by(pat_num=pat_num, clinic_id=clinic_uid).first()

            appt_id = appt_data.get('appointment_id') or str(uuid.uuid4())

            # Parse datetime fields
            appt_datetime = appt_data.get('appointment_datetime')
            if isinstance(appt_datetime, str):
                try:
                    appt_datetime = datetime.fromisoformat(appt_datetime)
                except ValueError:
                    appt_datetime = None

            sheet_date = appt_data.get('sheet_date')
            if isinstance(sheet_date, str):
                try:
                    sheet_date = datetime.strptime(sheet_date, '%Y-%m-%d').date()
                except ValueError:
                    sheet_date = None

            appointment = Appointment(
                id=appt_id,
                clinic_id=clinic_uid,
                patient_id=patient.id if patient else None,
                appointment_datetime=appt_datetime,
                sheet_date=sheet_date,
                spreadsheet_row=appt_data.get('spreadsheet_row'),
                practice=appt_data.get('practice'),
                carrier_name=appt_data.get('carrier_name'),
                verification_status=appt_data.get('insurance_verification_status'),
                verification_type=appt_data.get('verification_type'),
                process_result=appt_data.get('insurance_verification_process_result'),
                upload_status=appt_data.get('upload_status'),
                raw_data=appt_data
            )
            appointments_to_add.append(appointment)

        # Bulk add all appointments
        db.session.add_all(appointments_to_add)
        db.session.commit()

        return [appt.to_dict() for appt in appointments_to_add]

    @staticmethod
    def get_appointment(clinic_uid: str, appointment_id: str) -> Optional[Dict[str, Any]]:
        """Get an appointment by ID."""
        appt = Appointment.query.filter_by(id=appointment_id, clinic_id=clinic_uid).first()
        return appt.to_dict() if appt else None

    @staticmethod
    def update_appointment(
        clinic_uid: str,
        appointment_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update an appointment."""
        appt = Appointment.query.filter_by(id=appointment_id, clinic_id=clinic_uid).first()
        if not appt:
            return None

        field_mapping = {
            'insurance_verification_status': 'verification_status',
            'insurance_verification_process_result': 'process_result'
        }

        for key, value in updates.items():
            target_key = field_mapping.get(key, key)
            if hasattr(appt, target_key):
                setattr(appt, target_key, value)

        db.session.commit()
        return appt.to_dict()

    @staticmethod
    def delete_appointment(clinic_uid: str, appointment_id: str) -> bool:
        """Delete an appointment by ID."""
        appt = Appointment.query.filter_by(id=appointment_id, clinic_id=clinic_uid).first()
        if not appt:
            return False
        db.session.delete(appt)
        db.session.commit()
        return True


class TaskService:
    """Service class for Task CRUD operations."""

    @staticmethod
    def create_task(client_uid: str, clinic_uid: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task."""
        task_id = str(uuid.uuid4())
        
        new_task = Task(
            id=task_id,
            client_id=client_uid,
            clinic_id=clinic_uid,
            task_type=task_data.get('task_type'),
            status=task_data.get('status', 'pending'),
            priority=task_data.get('priority', 0),
            dates=task_data.get('dates', [])
        )
        
        db.session.add(new_task)
        db.session.commit()
        return new_task.to_dict()

    @staticmethod
    def update_task_status(task_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update task status and other fields."""
        task = Task.query.get(task_id)
        if not task:
            return None

        fields_to_exclude = {'id', 'task_id', 'created_at'}
        for key, value in updates.items():
            if hasattr(task, key) and key not in fields_to_exclude:
                setattr(task, key, value)
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return task.to_dict()

    @staticmethod
    def delete_task(task_id: str) -> bool:
        """Delete a task."""
        task = Task.query.get(task_id)
        if not task:
            return False
        
        db.session.delete(task)
        db.session.commit()
        return True


class ConfigService:
    """Service class for Configuration CRUD operations."""

    @staticmethod
    def create_or_update_config(client_uid: str, clinic_uid: str, config_name: str, yaml_content: str) -> Dict[str, Any]:
        """Create or update a configuration."""
        config = ClientConfig.query.filter_by(
            client_id=client_uid, 
            clinic_id=clinic_uid, 
            config_name=config_name
        ).first()

        if config:
            config.yaml_content = yaml_content
            config.updated_at = datetime.utcnow()
        else:
            config = ClientConfig(
                id=str(uuid.uuid4()),
                client_id=client_uid,
                clinic_id=clinic_uid,
                config_name=config_name,
                yaml_content=yaml_content
            )
            db.session.add(config)
        
        db.session.commit()
        return config.to_dict()

    @staticmethod
    def get_config(client_uid: str, clinic_uid: str, config_name: str) -> Optional[Dict[str, Any]]:
        """Get a configuration."""
        config = ClientConfig.query.filter_by(
            client_id=client_uid, 
            clinic_id=clinic_uid, 
            config_name=config_name
        ).first()
        return config.to_dict() if config else None

