[![Build Status](https://travis-ci.org/linw1995/weblog.svg?branch=master)](https://travis-ci.org/linw1995/weblog)&nbsp;&nbsp;[![Coverage Status](https://coveralls.io/repos/github/linw1995/weblog/badge.svg?branch=master)](https://coveralls.io/github/linw1995/weblog?branch=master)&nbsp;&nbsp;[![Code Issues](https://www.quantifiedcode.com/api/v1/project/ec93b3f8640740878a48e07f38aa6c25/badge.svg)](https://www.quantifiedcode.com/app/project/ec93b3f8640740878a48e07f38aa6c25)
# About weblog

weblog is powered by [Flask](http://flask.pocoo.org/).

It&#39;s started in 6 May, 2016

weblog aims to do it better, its features are as follow:

- multiple user
- roles: admin, moderator, user
- posts, tags, and categories
- messages
- change configurations by configuration file or environment variable

## Demo

![](README/01.png)

![](README/02.png)

![](README/03.png)

## Dependency

### Backend

        pip install -r requirements.txt

- [Flask](https://github.com/pallets/flask)
    - [Flask-Script](https://github.com/smurfix/flask-script)
    - [Flask-Login](https://github.com/maxcountryman/flask-login)
    - [Flask-SQLAlchemy](https://github.com/mitsuhiko/flask-sqlalchemy)
- [Markdown](http://daringfireball.net/projects/markdown/)

### Frontend

download to `app/static/js`

- [jQuery](https://github.com/jquery/jquery)
- [Moment.js](https://momentjs.com/)

## License

weblog is under MIT
