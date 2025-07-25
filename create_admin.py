from flask import Blueprint
from app import db
from app.models import User
from werkzeug.security import generate_password_hash

print("✅ create_admin.py loaded")

create_admin_bp = Blueprint('create_admin', __name__)

@create_admin_bp.route('/create_admin')
def create_admin():
    print("🔵 /create_admin route hit")

    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        return "⚠️ Admin user already exists."

    admin = User(username='admin', name='Admin User')
    admin.password_hash = generate_password_hash('admin123')  # set password securely
    admin.role = 'admin'
    db.session.add(admin)
    db.session.commit()
    return "✅ Admin created successfully with hashed password!"
