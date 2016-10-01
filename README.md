[![Build Status](https://travis-ci.org/ZsLinw/weblog.svg?branch=master)](https://travis-ci.org/ZsLinw/weblog)&nbsp;&nbsp;[![Coverage Status](https://coveralls.io/repos/github/ZsLinw/weblog/badge.svg?branch=master)](https://coveralls.io/github/ZsLinw/weblog?branch=master)&nbsp;&nbsp;[![Code Issues](https://www.quantifiedcode.com/api/v1/project/ec93b3f8640740878a48e07f38aa6c25/badge.svg)](https://www.quantifiedcode.com/app/project/ec93b3f8640740878a48e07f38aa6c25)
# About weblog

[weblog](https://github.com/ZsLinw/weblog) is powered by [Flask](http://flask.pocoo.org/).

It&#39;s started in 6 May, 2016

weblog aims to do it better, its features are as follow:

- multiple user
- roles: admin, moderator, user
- posts, short posts, comments, tags, and categories
- messages and mail
- markdown support
- admin interface
- change configurations by configuration file or environment variable
- Deploy with docker

## Demo

[weblog](http://web-log.daoapp.io)

## Dependency

### Backend

- Flask
    - Flask-Script
    - Flask-Login
    - Flask-WTF
    - Flask-Moment
    - Flask-SQLAlchemy
    - Flask-Migrate
    - Flask-Mail
    - Flask-Bootstrap
- WTForms
- Markdown

### Frontend

- jQuery
- BootStrap
    - [Bootswatch paper theme](http://bootswatch.com/paper/)
- [Editor.md](https://github.com/pandao/editor.md)

## License

weblog is under MIT
