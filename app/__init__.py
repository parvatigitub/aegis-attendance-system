from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
csrf = CSRFProtect(app)
migrate = Migrate(app, db)

login_manager.login_view = 'auth.login'

# Blueprints
from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.supervisor import supervisor_bp

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(supervisor_bp, url_prefix='/supervisor')

# Cache-Control
@app.after_request
def add_header(response):
    if 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# ✅ ✅ Admin Auto-Creation (Paste this at the END of file)
with app.app_context():
    from app.models import User
    from werkzeug.security import generate_password_hash

    try:
        existing_admin = User.query.filter_by(username='admin').first()
        if not existing_admin:
            admin = User(
                username='admin',
                name='Admin User',
                role='admin',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully.")
        else:
            print("ℹ️ Admin user already exists.")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
from app.routes.fix_admin import fix_admin_bp
app.register_blueprint(fix_admin_bp)

