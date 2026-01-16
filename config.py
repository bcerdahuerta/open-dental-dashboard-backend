import os

basedir = os.path.abspath(os.path.dirname(__file__))


# Flask configuration - PostgreSQL is required
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "devkey")
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]  # Fail fast if not set
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', './secrets/serviceAccountKey.json')
