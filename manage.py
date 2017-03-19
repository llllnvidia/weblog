# -*- coding: utf-8 -*-
import os
from flask_script import Manager, Shell, Server

from app import create_app, db
from app.models.post import Post, Category, Tag
from app.models.account import User

basedir = os.path.abspath(os.path.dirname(__file__))

app = create_app(os.getenv('WEBLOG_CONFIG', 'default'))

manager = Manager(app)


def make_shell_context():
    """add the shell context"""
    return dict(
        app=app, db=db, User=User, Post=Post, Category=Category, Tag=Tag)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command("runserver", Server(host='127.0.0.1', port=5000))
manager.add_command(
    "debug",
    Server(host='127.0.0.1', port=5000, use_debugger=True, use_reloader=True))


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    """Run deployment task"""
    db.drop_all()
    db.create_all()


if __name__ == '__main__':
    manager.run()
