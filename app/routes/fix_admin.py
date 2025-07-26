# app/routes/fix_admin.py
from flask import Blueprint
from app.models import User
from werkzeug.security import generate_password_hash
from app import db

fix_admin_bp = Blueprint('fix_admin', __name__)

@fix_admin_bp.route('/fix-admin-password', methods=["GET"])
def fix_admin_password():
    try:
        admin = User.query.filter_by(username='admin').first()
        if admin:
            admin.password_hash = generate_password_hash('admin123')
            db.session.commit()
            return "✅ Password reset successful. New password is 'admin123'."
        return "❌ Admin user not found."
    except Exception as e:
        return f"❌ Error: {str(e)}"
