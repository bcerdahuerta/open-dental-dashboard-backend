import os
from flask import Flask
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from extensions import db, swagger
from modules.clients.routes.client_routes import clients_bp
from modules.auth.routes.auth_routes import auth_bp
from modules.tasks.routes.tasks_routes import tasks_bp
from dotenv import load_dotenv

load_dotenv()

# Initialize Migrate at module level
migrate = Migrate()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Migrate
    # Import models to ensure they are registered with SQLAlchemy
    import models
    migrate.init_app(app, db)

    # Initialize Swagger for API documentation
    swagger.init_app(app)

    JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(clients_bp, url_prefix="/api/v1/clients")
    app.register_blueprint(tasks_bp, url_prefix="/api/v1/tasks")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
