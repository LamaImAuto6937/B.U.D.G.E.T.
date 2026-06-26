import os
import hashlib
import random
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    # Generate Random Secret Key
    salt = os.urandom(16)
    key = random.randint(0, 10000)
    secret_key = hashlib.sha512(salt + str(key).encode('utf-8')).hexdigest()

    app = Flask(__name__)
    app.secret_key = secret_key
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

    # Blueprints registrieren
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.expense import expense_bp
    from app.routes.budget import budget_bp
    from app.routes.savings import savings_bp
    from app.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(budget_bp)
    app.register_blueprint(savings_bp)
    app.register_blueprint(settings_bp)

    return app
