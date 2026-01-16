from . import auth_bp
from ..controllers.auth_controller import login

auth_bp.add_url_rule("/login", view_func=login, methods=["POST"])
