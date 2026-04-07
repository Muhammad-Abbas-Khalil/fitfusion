import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:11223344@localhost:5432/fitfusion_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
