from flask import Flask
from config import Config
from .extensions import db, migrate

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints here
    # from .routes import main
    # app.register_blueprint(main)

    return app
