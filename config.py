import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://localhost/fitfusion_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False