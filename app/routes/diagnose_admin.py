# app/routes/diagnose_admin.py
from flask import Blueprint
from app.models import User
from werkzeug.security import generate_password_hash
from app import db

diagnose_admin_bp = Blueprint('diagnose_admin', __name__)

@diagnose_admin_bp.route('/fix-admin-password')
def fix_admin_password():
    try:
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.password_hash = generate_password_hash('admin123')
            db.session.commit()
            return "✅ Password updated to 'admin123'."
        return "❌ Admin user not found."
    except Exception as e:
        return f"❌ Error: {str(e)}"
