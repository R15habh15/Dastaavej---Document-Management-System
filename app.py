from flask import Flask
from config import Config
from extensions import db, login_manager, csrf, migrate, mail
from routes.auth import auth_bp
from routes.citizen import citizen_bp
from routes.agency import agency_bp
from routes.error import error_bp
from routes.main import main_bp
import os
from datetime import timedelta

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Add verification cache
    app.config['VERIFICATION_CACHE'] = {}
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Set session timeout (30 minutes)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Fix: Redirect unauthenticated users to the login page
    setattr(login_manager, 'login_view', 'auth.login')
    login_manager.login_message_category = "warning"

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(citizen_bp, url_prefix="/citizen")
    app.register_blueprint(agency_bp, url_prefix="/agency")
    app.register_blueprint(error_bp)
    app.register_blueprint(main_bp)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)