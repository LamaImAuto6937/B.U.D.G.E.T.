import os
from datetime import timedelta
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__)
    
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if secret_key:
        app.secret_key = secret_key
    else:
        raise RuntimeError('FLASK_SECRET_KEY is Missing in .env ! Run  python -c "import secrets; print(secrets.token_hex(32))"  to generate a new one!')
    
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

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
