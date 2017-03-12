# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api
from flask_login import LoginManager

from config import config

# extension
db = SQLAlchemy()
api = Api()
login_manager = LoginManager()


def create_app(config_name):
    """create flask app instance"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    login_manager.init_app(app)
    app.jinja_env.trim_blocks = True

    from .main import main as blueprint_main
    from .rest import blueprint_api
    app.register_blueprint(blueprint_main)
    app.register_blueprint(blueprint_api, url_prefix="/api")

    return app
