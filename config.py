import os

class Config:
    SECRET_KEY = 'shivam_attendnce_models'

    if os.environ.get("RENDER") == "true":
        SQLALCHEMY_DATABASE_URI = 'postgresql://attendance_db_2bae_user:A4GORsQuyhwOsWwV7F8G6gr0gMAmXUS4@dpg-d21gphadbo4c73e57scg-a/attendance_db_2bae'
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:12345@localhost:5432/attendance_db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # ✅ Add admin username and password from environment
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
