# -*- coding: utf-8 -*-
# !/usr/bin/env python

import os
import sys
from datetime import datetime

from flask.ext.migrate import Migrate, MigrateCommand
from flask.ext.script import Manager, Shell, Server

from app import create_app, db
from app.models.post import User, Post, Category
from app.models.account import Role, User

basedir = os.path.abspath(os.path.dirname(__file__))

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
    if not os.path.isfile(app.config['SQLALCHEMY_DATABASE_URI'][10:]):
        db.create_all()
        print 'Datebase created.'
        Role.insert_roles()
        print 'insert Roles.'
        User.add_self_follows()
        print 'User config.'
        User.add_admin()
        print 'add admin :'\
            '\nemail=Admin@CodeBlog.com'\
            '\npassword=1234'
        Category.add_none()
        print 'Category insert None.'
    else:
        print 'database already exists!'


@manager.command
def init_migrations():
    from flask.ext.migrate import init
    if not os.path.isdir(os.getenv('MIGRATIONS', basedir+'/migrations')):
        init(directory=os.getenv('MIGRATIONS',  basedir+'/migrations'))
        print 'create migration :' + os.getenv('MIGRATIONS', basedir+'/migrations')
    else:
        print 'migration already exists! path:' + os.getenv('MIGRATIONS', basedir+'/migrations')


@manager.command
def migrate_migrations():
    from flask.ext.migrate import migrate
    if os.path.exists(os.getenv('MIGRATIONS', basedir + '/migrations')):
        migrate(directory=os.getenv('MIGRATIONS', basedir + '/migrations'),message=str(datetime.utcnow()))
        print 'migrate database :' + os.getenv('MIGRATIONS', basedir + '/migrations')
    else:
        print 'Can\'t find :' + os.getenv('MIGRATIONS', basedir + '/migrations')


@manager.command
def upgrade_migrations():
    from flask.ext.migrate import upgrade
    if os.path.exists(os.getenv('MIGRATIONS', basedir+'/migrations')):
        upgrade(directory=os.getenv('MIGRATIONS', basedir+'/migrations'))
        print 'upgrade database :' + os.getenv('MIGRATIONS', basedir+'/migrations')
    else:
        print 'Can\'t find :' + os.getenv('MIGRATIONS', basedir+'/migrations')


@manager.command
def downgrade_migrations():
    from flask.ext.migrate import downgrade
    if os.path.exists(os.getenv('MIGRATIONS', basedir+'/migrations')):
        downgrade(directory=os.getenv('MIGRATIONS', basedir+'/migrations'))
        print 'downgrade database :' + os.getenv('MIGRATIONS', basedir+'/migrations')
    else:
        print 'Can\'t find :' + os.getenv('MIGRATIONS', basedir+'/migrations')


if __name__ == '__main__':
    manager.run()
