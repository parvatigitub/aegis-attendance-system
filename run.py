import os
from app import app
from flask_migrate import upgrade

with app.app_context():
    upgrade()  # ✅ Apply migrations when the app starts

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
