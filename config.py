# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(16)
    POSTS_PER_PAGE = 10
    IMG_PATH = os.environ.get("IMG_PATH", basedir + r"\app\static")
    BUNDLE_ERRORS = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL",
        r"sqlite:///" + os.path.join(basedir, "data-dev-temporary.sqlite"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DebugConfig(DevelopmentConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL",
        r"sqlite:///" + os.path.join(basedir, 'data-dev-temporary.sqlite'))
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    TEMPLATES_AUTO_RELOAD = True


class TestingConfig(Config):
    TESTING = True
    SERVER_NAME = '127.0.0.1:5000'
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL",
        r"sqlite:///" + os.path.join(basedir, 'data-test-temporary.sqlite'))
    SQLALCHEMY_TRACK_MODIFICATIONS = True


config = {
    'development': DevelopmentConfig,
    'debug': DebugConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
