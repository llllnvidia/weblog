# -*- coding: utf-8 -*-
# !/usr/bin/env python

import sys
import os
from app import create_app, db
from app.models import User, Role, Post, Category
from flask.ext.script import Manager, Shell, Server
from flask.ext.migrate import Migrate, MigrateCommand

reload(sys)
sys.setdefaultencoding('utf-8')

app = create_app(os.getenv('CODEBLOG_CONFIG') or 'default')

migrate = Migrate(app, db)
manager = Manager(app)

def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Post=Post, Category=Category)

manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(
    use_debugger=True,
    use_reloader=True,
    host='127.0.0.1',
    port=5000)
)

@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)

@manager.command
def deploy():
    """Run deployment task"""
    from flask.ext.migrate import upgrade, init
    if os.path.isfile(app.config['SQLALCHEMY_DATABASE_URI'][10:]):
        if os.path.isdir(os.getenv('MIGRATIONS', 'migrations')):
            upgrade(directory=os.getenv('MIGRATIONS', 'migrations'))
            Role.insert_roles()
            User.add_self_follows()
        else:
            init(directory=os.getenv('MIGRATIONS', 'migrations'))
            Role.insert_roles()
            User.add_self_follows()
    else:
        db.create_all()
        Role.insert_roles()
        User.add_self_follows()
        User.add_admin()
        Category.add_none()
    print 'Deploy!'

if __name__ == '__main__':
    manager.run()
