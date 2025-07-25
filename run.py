from app import app
from flask_migrate import upgrade

with app.app_context():
    upgrade()  # Apply all migrations
