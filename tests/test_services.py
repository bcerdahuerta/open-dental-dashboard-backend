"""
Unit tests for the Service Layer.
Verifies ClientService and AppointmentService functionality.
"""
import pytest
import uuid
from datetime import datetime

from app import create_app
from extensions import db
from models import Client, Clinic, Patient, Appointment
from modules.clients.services.services import ClientService, AppointmentService


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Provide an application context for tests."""
    with app.app_context():
        yield


class TestClientService:
    """Tests for ClientService."""

    def test_create_client_success(self, app_context):
        """Test that ClientService.create_client successfully commits to the DB."""
        client_data = {
            'client_name': 'Test Dental Practice',
            'active': True,
            'ccc_username': 'testuser',
            'ccc_password': 'testpass'
        }

        result = ClientService.create_client(client_data)

        # Verify the result contains expected data
        assert result is not None
        assert result['client_name'] == 'Test Dental Practice'
        assert result['active'] is True
        assert 'id' in result

        # Verify it was actually persisted to DB
        db_client = Client.query.get(result['id'])
        assert db_client is not None
        assert db_client.client_name == 'Test Dental Practice'

    def test_create_client_with_custom_id(self, app_context):
        """Test that ClientService respects a provided client_uid."""
        custom_id = str(uuid.uuid4())
        client_data = {
            'client_uid': custom_id,
            'client_name': 'Custom ID Practice'
        }

        result = ClientService.create_client(client_data)

        assert result['id'] == custom_id
        assert Client.query.get(custom_id) is not None

    def test_update_client_success(self, app_context):
        """Test that ClientService.update_client updates fields correctly."""
        # Create a client first
        client_data = {'client_name': 'Original Name', 'active': False}
        created = ClientService.create_client(client_data)

        # Update it
        result = ClientService.update_client(created['id'], {'active': True})

        assert result is not None
        assert result['active'] is True

        # Verify in DB
        db_client = Client.query.get(created['id'])
        assert db_client.active is True

    def test_update_client_not_found(self, app_context):
        """Test that updating a non-existent client returns None."""
        result = ClientService.update_client('non-existent-id', {'active': True})
        assert result is None


class TestAppointmentService:
    """Tests for AppointmentService."""

    @pytest.fixture
    def setup_clinic(self, app_context):
        """Create a client and clinic for appointment tests."""
        client = Client(
            id=str(uuid.uuid4()),
            client_name='Test Client'
        )
        db.session.add(client)

        clinic = Clinic(
            id=str(uuid.uuid4()),
            client_id=client.id,
            clinic_name='Test Clinic'
        )
        db.session.add(clinic)
        db.session.commit()

        return {'client': client, 'clinic': clinic}

    def test_create_appointments_bulk_success(self, app_context, setup_clinic):
        """Test that AppointmentService.create_appointments_bulk creates multiple records."""
        clinic = setup_clinic['clinic']

        appointments_data = [
            {
                'patnum': 'PAT001',
                'patient_first_name': 'John',
                'patient_last_name': 'Doe',
                'carrier_name': 'Delta Dental',
                'insurance_verification_status': 'pending'
            },
            {
                'patnum': 'PAT002',
                'patient_first_name': 'Jane',
                'patient_last_name': 'Smith',
                'carrier_name': 'Cigna',
                'insurance_verification_status': 'verified'
            },
            {
                'patnum': 'PAT003',
                'patient_first_name': 'Bob',
                'patient_last_name': 'Johnson',
                'carrier_name': 'Aetna',
                'insurance_verification_status': 'pending'
            }
        ]

        result = AppointmentService.create_appointments_bulk(clinic.id, appointments_data)

        # Verify the return value
        assert len(result) == 3

        # Verify appointments were persisted
        db_appointments = Appointment.query.filter_by(clinic_id=clinic.id).all()
        assert len(db_appointments) == 3

        # Verify patients were created
        db_patients = Patient.query.filter_by(clinic_id=clinic.id).all()
        assert len(db_patients) == 3

    def test_create_appointments_bulk_reuses_existing_patients(self, app_context, setup_clinic):
        """Test that bulk creation reuses existing patients instead of duplicating."""
        clinic = setup_clinic['clinic']

        # Create an existing patient
        existing_patient = Patient(
            pat_num='PAT001',
            clinic_id=clinic.id,
            first_name='Existing',
            last_name='Patient'
        )
        db.session.add(existing_patient)
        db.session.commit()

        appointments_data = [
            {
                'patnum': 'PAT001',  # Should reuse existing patient
                'carrier_name': 'Delta Dental'
            },
            {
                'patnum': 'PAT002',  # Should create new patient
                'patient_first_name': 'New',
                'patient_last_name': 'Patient',
                'carrier_name': 'Cigna'
            }
        ]

        result = AppointmentService.create_appointments_bulk(clinic.id, appointments_data)

        assert len(result) == 2

        # Should still only have 2 patients (1 existing + 1 new)
        db_patients = Patient.query.filter_by(clinic_id=clinic.id).all()
        assert len(db_patients) == 2

    def test_create_appointments_bulk_empty_list(self, app_context, setup_clinic):
        """Test that bulk creation handles empty lists gracefully."""
        clinic = setup_clinic['clinic']

        result = AppointmentService.create_appointments_bulk(clinic.id, [])

        assert result == []
        assert Appointment.query.filter_by(clinic_id=clinic.id).count() == 0
