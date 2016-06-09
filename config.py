# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bshghadasssdfjaskdjfhaklsfasdjfl'
    SQLALCEMY_COMMIT_ON_TEARDOWN = True
    ADMIN = os.environ.get('ADMIN', 'Admin')
    MAIL_SUBJECT_PREFIX = '[CodeBlog]'
    MAIL_SENDER = str(ADMIN) + ' <' + str(os.environ.get('MAIL_USERNAME', 'admin@codeblog.com')) + '>'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    POSTS_PER_PAGE = 10
    FOLLOWERS_PER_PAGE = 10
    COMMENTS_PER_PAGE = 10
    DIALOGUE_PER_PAGE = 10
    IMG_PATH = os.environ.get('IMG_PATH', basedir)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = False
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
                             
                             
class DebugConfig(DevelopmentConfig):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {
    'development': DevelopmentConfig,
    'debug' : DebugConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    'default': DevelopmentConfig
}
