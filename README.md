[![Build Status](https://travis-ci.org/linw1995/weblog.svg?branch=master)](https://travis-ci.org/linw1995/weblog)&nbsp;&nbsp;[![Coverage Status](https://coveralls.io/repos/github/linw1995/weblog/badge.svg?branch=master)](https://coveralls.io/github/linw1995/weblog?branch=master)&nbsp;&nbsp;[![Code Issues](https://www.quantifiedcode.com/api/v1/project/ec93b3f8640740878a48e07f38aa6c25/badge.svg)](https://www.quantifiedcode.com/app/project/ec93b3f8640740878a48e07f38aa6c25)
# About weblog

weblog is powered by [Flask](http://flask.pocoo.org/).

It&#39;s started in 6 May, 2016

weblog aims to do it better, its features are as follow:

- multiple user
- roles: admin, moderator, user
- posts, comments, tags, and categories
- messages and mail
- admin interface
- change configurations by configuration file or environment variable
- Deploy with docker

## Demo

[==> Portal to Demo <==](http://web-log.daoapp.io)

Using Dock to deploy on DaoCloud.

Related Doc : [python-docker](http://docs.daocloud.io/python-docker)


## Dependency

### Backend

- [Flask](https://github.com/pallets/flask)
    - [Flask-Script](https://github.com/smurfix/flask-script)
    - [Flask-Login](https://github.com/maxcountryman/flask-login)
    - [Flask-WTF](https://github.com/lepture/flask-wtf)
    - [Flask-Moment](https://github.com/miguelgrinberg/Flask-Moment)
    - [Flask-SQLAlchemy](https://github.com/mitsuhiko/flask-sqlalchemy)
    - [Flask-Migrate](https://github.com/miguelgrinberg/Flask-Migrate)
    - [Flask-Mail](https://github.com/mattupstate/flask-mail)
    - [Flask-Bootstrap](https://github.com/mbr/flask-bootstrap)
    - [Flask-Cache](https://github.com/thadeusb/flask-cache)
- [WTForms](https://github.com/wtforms/wtforms)
- [Markdown](http://daringfireball.net/projects/markdown/)

### Frontend

- [jQuery](https://github.com/jquery/jquery)
- [Bootstrap](https://github.com/twbs/bootstrap)
    - [Bootswatch paper theme](http://bootswatch.com/paper/)
- [Editor.md](https://github.com/pandao/editor.md)

## License

weblog is under MIT
