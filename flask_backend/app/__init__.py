from flask import Flask
from flask_cors import CORS
from app.routes import main_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    CORS(app)

    # Register routes
    app.register_blueprint(main_routes)

    return app
