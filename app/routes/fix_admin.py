# app/routes/fix_admin.py
from flask import Blueprint
from app.models import User
from app import db
from werkzeug.security import generate_password_hash

fix_admin_bp = Blueprint('fix_admin', __name__)

@fix_admin_bp.route('/fix-admin-password')
def fix_admin_password():
    admin = User.query.filter_by(username='admin').first()
    if admin:
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()
        return "✅ Admin password reset to 'admin123'"
    return "❌ Admin user not found"
