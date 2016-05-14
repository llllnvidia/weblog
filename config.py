# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'badass'
    SQLALCEMY_COMMIT_ON_TEARDOWN = True
    CODEBLOG_MAIL_SUBJECT_PREFIX = '[CodeBlog]'
    CODEBLOG_MAIL_SENDER = 'Shuanmu <13275009504@163.com>'
    CODEBLOG_ADMIN = os.environ.get('CODEBLOG_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    CODEBLOG_POSTS_PER_PAGE = 10
    CODEBLOG_FOLLOWERS_PER_PAGE = 10
    CODEBLOG_COMMENTS_PER_PAGE = 10
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USERNAME = os.environ.get('CODEBLOG_MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('CODEBLOG_MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir,'data-dev.sqlite')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir,'data-test.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir,'data.sqlite')

config = {
    'development':DevelopmentConfig,
    'testing':TestingConfig,
    'production':ProductionConfig,

    'default':DevelopmentConfig
}
