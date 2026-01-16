"""
Admin CLI for Client and Clinic Onboarding.

This script provides administrative commands to create clients and clinics
directly in the PostgreSQL database via the Service Layer.

Usage:
    python -m scripts.admin_cli list-clients
    python -m scripts.admin_cli create-client --name "Demo Dental Group"
    python -m scripts.admin_cli add-clinic --client-id <UUID> --name "Downtown" --sheet-id <SPREADSHEET_ID>

Examples:
    # Create a new client
    python -m scripts.admin_cli create-client --name "Demo Dental Group"
    # Output: Created Client: 'Demo Dental Group' with UUID: <UUID>

    # List all clients
    python -m scripts.admin_cli list-clients

    # Add a clinic to a client
    python -m scripts.admin_cli add-clinic --client-id abc123 --name "Downtown" --sheet-id 1ABC...XYZ
"""
import argparse
import os
import sys

# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import Client
from modules.clients.services.services import ClientService, ClinicService
from shared.loggers import DentalRobotLogger


def list_clients():
    """List all clients with ID, Name, and Active status."""
    clients = Client.query.all()
    
    if not clients:
        print("No clients found in the database.")
        return
    
    print(f"{'ID':<40} {'Name':<30} {'Active':<8}")
    print("-" * 80)
    
    for client in clients:
        active_status = "Yes" if client.active else "No"
        print(f"{client.id:<40} {client.name:<30} {active_status:<8}")
    
    print(f"\nTotal: {len(clients)} client(s)")


def create_client(name: str) -> str:
    """
    Create a new client with the given name.
    
    Args:
        name: The client's name.
        
    Returns:
        The new client's UUID.
    """
    # Initialize logger for audit trail
    logger = DentalRobotLogger(
        client_uid="admin",
        clinic_uid="cli",
        pipeline="admin_cli"
    )
    
    # Check if client with this name already exists
    existing_client = Client.query.filter_by(name=name).first()
    if existing_client:
        print(f"[ERROR] A client with the name '{name}' already exists (ID: {existing_client.id}).")
        print("Please use a different name or update the existing client.")
        return None
    
    try:
        client_data = {
            'name': name,
            'active': True
        }
        
        new_client = ClientService.create_client(client_data)
        client_id = new_client['id']
        
        # Log for audit trail
        logger.info(f"Created new client '{name}' with ID: {client_id}", save_log=True)
        
        print(f"[SUCCESS] Created Client: '{name}' with UUID: {client_id}")
        return client_id
        
    except Exception as e:
        logger.error(f"Failed to create client '{name}': {str(e)}", save_log=True)
        print(f"[ERROR] Failed to create client: {str(e)}")
        return None


def add_clinic(client_id: str, name: str, sheet_id: str) -> str:
    """
    Add a clinic to an existing client.
    
    Args:
        client_id: The client's UUID.
        name: The clinic's name.
        sheet_id: The Google Spreadsheet ID for this clinic.
        
    Returns:
        The new clinic's UUID.
    """
    # Initialize logger for audit trail
    logger = DentalRobotLogger(
        client_uid=client_id,
        clinic_uid="new",
        pipeline="admin_cli"
    )
    
    # Verify the client exists
    client = Client.query.get(client_id)
    if not client:
        # Try to find by name as fallback
        client = Client.query.filter_by(name=client_id).first()
        if client:
            client_id = client.id
        else:
            print(f"[ERROR] Client not found: '{client_id}'")
            print("Use 'list-clients' to see available clients.")
            return None
    
    try:
        clinic_data = {
            'clinic_name': name,
            'spreadsheet_id': sheet_id
        }
        
        new_clinic = ClinicService.create_clinic(client_id, clinic_data)
        clinic_id = new_clinic['id']
        
        # Log for audit trail
        logger.info(
            f"Created clinic '{name}' (ID: {clinic_id}) for client '{client.name}'",
            save_log=True
        )
        
        print(f"[SUCCESS] Created Clinic: '{name}'")
        print(f"  Clinic UUID: {clinic_id}")
        print(f"  Client: {client.name} ({client_id})")
        print(f"  Spreadsheet ID: {sheet_id}")
        return clinic_id
        
    except Exception as e:
        logger.error(f"Failed to create clinic '{name}': {str(e)}", save_log=True)
        print(f"[ERROR] Failed to create clinic: {str(e)}")
        return None


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Admin CLI for Client and Clinic onboarding.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.admin_cli list-clients
  python -m scripts.admin_cli create-client --name "Demo Dental Group"
  python -m scripts.admin_cli add-clinic --client-id <UUID> --name "Downtown" --sheet-id <ID>
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # list-clients command
    subparsers.add_parser("list-clients", help="List all clients")
    
    # create-client command
    create_parser = subparsers.add_parser("create-client", help="Create a new client")
    create_parser.add_argument(
        "--name",
        required=True,
        help="Name of the client (dental group/organization)"
    )
    
    # add-clinic command
    clinic_parser = subparsers.add_parser("add-clinic", help="Add a clinic to a client")
    clinic_parser.add_argument(
        "--client-id",
        required=True,
        help="Client UUID or name"
    )
    clinic_parser.add_argument(
        "--name",
        required=True,
        help="Name of the clinic"
    )
    clinic_parser.add_argument(
        "--sheet-id",
        required=True,
        help="Google Spreadsheet ID for this clinic"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Initialize Flask app context
    app = create_app()
    
    with app.app_context():
        if args.command == "list-clients":
            list_clients()
        
        elif args.command == "create-client":
            create_client(args.name)
        
        elif args.command == "add-clinic":
            add_clinic(args.client_id, args.name, args.sheet_id)


if __name__ == "__main__":
    main()
