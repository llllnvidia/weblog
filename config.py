# -*- coding: utf-8 -*-
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or \
                 r"\x87\xb7t\xcc\x84\x1e\xff\n{IPF\xa9s\xf2\xf0\x8d9\xde'\x12\x1c\xa5\xe6"
    SQLALCEMY_COMMIT_ON_TEARDOWN = True
    DB_QUERY_TIMEOUT = 2
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
    SQLALCHEMY_RECORD_QUERIES = True
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = 25
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.MAIL_USERNAME],
            subject=cls.MAIL_SUBJECT_PREFIX + ' Application Info',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.INFO)
        app.logger.addHandler(mail_handler)


class DebugConfig(DevelopmentConfig):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
    SERVER_NAME = '127.0.0.1:5000'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')


config = {
    'development': DevelopmentConfig,
    'debug': DebugConfig,
    'testing': TestingConfig,

    'default': DevelopmentConfig
}
