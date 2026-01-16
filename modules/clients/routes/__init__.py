from flask import Blueprint

clients_bp = Blueprint('clients', __name__)

from . import client_routes
