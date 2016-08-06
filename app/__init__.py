# -*- coding: utf-8 -*-
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_cache import Cache
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'
login_manager.login_message = '你必须登录才能到达此页面。'
cache = Cache()


def create_app(config_name):
    """create flask app instance"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    login_manager.init_app(app)
    db.init_app(app)
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})
    app.jinja_env.trim_blocks = True

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    from .post import post as post_blueprint
    app.register_blueprint(post_blueprint)
    from .admin_manager import admin_manager as admin_manager_blueprint
    app.register_blueprint(admin_manager_blueprint, url_prefix='/admin_manager')

    return app
