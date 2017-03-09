# -*- coding:utf-8 -*-
from datetime import datetime
from elizabeth import Personal, Text
from sqlalchemy.sql.expression import func
from random import choice, randint

from manage import app, db
from app.models.post import Post, Category, Tag
from app.models.account import Role, User

sql_expression_rand = func.random if app.config.get("SQLALCHEMY_DATABASE_URI").startswith("sqlite") else func.rand


def basic_deploy():
    Role.insert_roles()
    administrator = Role.query.filter_by(name="Administrator").first()
    admin = User(username="admin",
                 email="admin@weblog.com",
                 password="admin",
                 role=administrator)
    admin.save()
    category_default_parent = Category(name="")
    category_default_parent.save()
    category_default = Category(name="Other", parent=category_default_parent)
    category_default.save()


def bootstrap_user(count=60, locale="en"):
    person = Personal(locale)
    genders = ["male", "female"]
    for _ in range(count):
        while True:
            username = person.name(gender=genders[_ % 2])
            if User.query.filter_by(username=username).first() is None:
                break
        email = username.replace(" ", "_") + "@weblog.com"
        new = User(username=username,
                   email=email,
                   password=person.password())
        db.session.add(new)
    db.session.commit()


def bootstrap_tag(count=80, locale="en"):
    text = Text(locale)
    for _ in range(count):
        while True:
            name = text.word()
            if Tag.query.filter_by(name=name).first() is None:
                break
        new = Tag(name=name)
        db.session.add(new)
    db.session.commit()


def bootstrap_category(count=40, locale="en"):
    text = Text(locale)
    default_parent = Category.query.get(1)
    for _ in range(count):
        while True:
            name = text.word()
            if Category.query.filter_by(name=name).first() is None:
                break
        new = Category(name=name)
        if _ % 2:
            parent = Category.query.order_by(sql_expression_rand()).first()
            new.parent_category = parent
        else:
            new.parent_category = default_parent
        db.session.add(new)
    db.session.commit()


def bootstrap_post(count=400, locale="en"):
    text = Text(locale)
    box_summary_box = [1, 2, 3]
    box_article_box = [7, 8, 9]
    author_count = int(User.query.count() / 4)
    tag_count = int(Tag.query.count() / 4)
    authors = list()
    tags = list()
    category_default = Category.query.filter_by(name="其它").first()

    for _ in range(count):
        timestamp = datetime(year=randint(1995, 2017), month=randint(1, 12), day=randint(1, 28), hour=randint(0, 23),
                             minute=randint(0, 59), second=randint(0, 59), microsecond=randint(0, 999999))
        if _ % author_count == 0:
            authors = User.query.order_by(sql_expression_rand()).limit(author_count).all()
        if _ % tag_count == 0:
            tags = Tag.query.order_by(sql_expression_rand()).limit(tag_count).all()
        new = Post(author=authors[_ % author_count],
                   title=text.title(),
                   summary=text.text(choice(box_summary_box)),
                   body=text.text(choice(box_article_box)),
                   timestamp=timestamp,
                   last_edit=timestamp,
                   count=randint(0, 10000))
        post_tags = [tag for no, tag in enumerate(tags) if no < _ % 4]
        new.tags.extend(post_tags)
        if _ % 3 == 0:
            category = Category.query.order_by(sql_expression_rand()).first()
            new.category = category
        else:
            new.category = category_default
        db.session.add(new)
    db.session.commit()


with app.app_context():
    db.drop_all()
    db.create_all()
    basic_deploy()
    bootstrap_user()
    bootstrap_tag()
    bootstrap_category()
    bootstrap_post()