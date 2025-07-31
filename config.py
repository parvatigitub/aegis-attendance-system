import os

class Config:
    SECRET_KEY = 'shivam_attendnce_models'
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345@localhost:5432/attendance_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
