from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = 'your-secret-key-here'  # In production, use a secure secret key

    # Ensure instance directory exists
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    db.init_app(app)

    from .models import models
    with app.app_context():
        db.create_all()

    from app.controllers.auth_controller import auth_bp
    from app.controllers.views_controller import views_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(views_bp)

    return app
