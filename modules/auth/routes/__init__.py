from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

# Importa las rutas del módulo de autenticación
from . import auth_routes
