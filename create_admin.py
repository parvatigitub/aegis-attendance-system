# create_admin.py

from flask import Blueprint
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

create_admin_bp = Blueprint('create_admin', __name__)

@create_admin_bp.route('/create_admin')
def create_admin():
    # Check if admin already exists
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        return "⚠️ Admin user already exists."

    # Create admin user
    hashed_pw = generate_password_hash('admin123')
    admin = User(username='admin', name='Admin User', role='admin', password_hash=hashed_pw)
    db.session.add(admin)
    db.session.commit()
    return "✅ Admin created successfully!"
