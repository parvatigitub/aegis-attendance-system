import os

from app import app
from flask_migrate import upgrade

if __name__ == '__main__':
    with app.app_context():   # ✅ Ye line application context activate karega
        upgrade()             # ✅ Ye migration apply karega
    app.run()
app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))