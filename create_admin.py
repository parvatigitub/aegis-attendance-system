from flask import Blueprint
from app import db, create_app
from app.models import User

create_admin_bp = Blueprint('create_admin', __name__)

@create_admin_bp.route('/create-admin')
def create_admin():
    # Check if admin already exists
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        return "⚠️ Admin user already exists."

    # Create admin user with hashed password
    admin = User(username='admin', name='Admin User')
    admin.set_password('admin123')
    admin.role = 'admin'
    db.session.add(admin)
    db.session.commit()
    return "✅ Admin created successfully with hashed password!"
