import os

from app import app
from flask_migrate import upgrade

if __name__ == '__main__':
    with app.app_context():   # ✅ Activate application context
        upgrade()             # ✅ Apply migrations

    # ✅ Correct: Only one app.run with proper host and port for Render
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
