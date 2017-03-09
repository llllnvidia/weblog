# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_restful import Api

from config import config

csrf = CSRFProtect()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = '你必须登录才能到达此页面。'
api = Api()


def create_app(config_name):
    """create flask app instance"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    csrf.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    app.jinja_env.trim_blocks = True

    from .main import main as blueprint_main
    from .rest import blueprint_api
    app.register_blueprint(blueprint_main)
    app.register_blueprint(blueprint_api, url_prefix="/api")

    return app
