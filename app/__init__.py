# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import config

# extension
db = SQLAlchemy()


def create_app(config_name):
    """create flask app instance"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    app.jinja_env.trim_blocks = True

    from .main import main as blueprint_main
    app.register_blueprint(blueprint_main)

    return app
