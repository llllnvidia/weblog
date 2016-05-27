# -*- coding: utf-8 -*-
from datetime import datetime

import bleach
from markdown import markdown

from app import db, login_manager
from app.models.account import User, AnonymousUser

posttags = db.Table('posttags',
                    db.Column('tags_id', db.Integer, db.ForeignKey('tags.id')),
                    db.Column('posts_id', db.Integer, db.ForeignKey('posts.id'))
                    )


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_article = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    title = db.Column(db.Text)
    summary = db.Column(db.Text)
    summary_html = db.Column(db.Text)
    last_edit = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
                               foreign_keys=[category_id],
                               backref=db.backref('posts', lazy='dynamic'))
    tags = db.relationship('Tag',
                           secondary=posttags,
                           backref=db.backref('posts', lazy='dynamic'))

    def __repr__(self):
        return '<Post %s Author %s>' % (self.title, User.query.filter_by(id=self.author_id).first().username)

    def ping(self):
        self.last_edit = datetime.utcnow()
        db.session.add(self)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def tag(self, tag):
        if not self.is_taging(tag):
            self.tags.append(tag)

    def untag(self, tag):
        if self.is_taging(tag):
            self.tags.remove(tag)

    def is_taging(self, tag):
        return tag in self.tags

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul', 'img', 'span',
                        'h1', 'h2', 'h3', 'p', 'tr', 'td', 'table', 'tbody', 'colgroup', 'col', 'thead', 'th']
        attrs = {
            '*': ['class'],
            'ol': ['class'],
            'li': ['rel'],
            'span': ['class'],
            'a': ['href', 'rel'],
            'img': ['src', 'alt'],
            'code': ['class', 'style']
        }

        a = value.split("\n")
        if len(a) > 15:
            b = []
            for i in range(15):
                if i < len(a):
                    b.append(a[i])
            target.summary = '\n'.join(b)
        else:
            target.summary = ""
        
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, attributes=attrs, strip=True))

        target.summary_html = bleach.linkify(bleach.clean(
            markdown(target.summary, output_format='html'),
            tags=allowed_tags, attributes=attrs, strip=True))


db.event.listen(Post.body, 'set', Post.on_changed_body)

login_manager.anonymous_user = AnonymousUser


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


db.event.listen(Comment.body, 'set', Comment.on_changed_body)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    parentid = db.Column(db.Integer, db.ForeignKey('category.id'))
    parentcategory = db.relationship('Category', uselist=False, remote_side=[id],
                                     backref=db.backref('soncategorys', uselist=True))

    def __init__(self, name, parentcategory=None):
        self.name = name
        self.parentcategory = parentcategory

    def __repr__(self):
        return '<Category %s Parent %s Son %s>' % (self.name,
                                                   Category.query.filter_by(id=self.parentid).first().name,
                                                   [cg.name for cg in self.soncategorys])

    @staticmethod
    def add_none():
        none = Category(name=u'None')
        none.save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        for post in self.posts:
            post.category_id = 1
            post.save()
        db.session.delete(self)
        db.session.commit()

    def posts_count(self, query=None):
        if query:
            count = query.filter(Post.category == self).count()
            sum = 0
            for category in self.soncategorys:
                sum = sum + query.filter(Post.category == category).count()
        else:
            count = self.posts.count()
            sum = 0
            for category in self.soncategorys:
                sum = sum + category.posts_count()
        count = count + sum
        return count

    def posts_query(self, query=None):
        if query:
            if self.soncategorys:
                posts = query.filter(Post.category == self)
                for soncategory in self.soncategorys:
                    query = query.filter(Post.category == soncategory)
                    if query.all() and posts.all():
                        posts = posts.union(query)
                    elif query.all():
                        posts = query
                    else:
                        posts = None
            else:
                posts = query.filter(Post.category == self)
        else:
            if self.soncategorys:
                posts = Post.query.filter(Post.category == self)
                for soncategory in self.soncategorys:
                    posts = posts.union(Post.filter(Post.category == soncategory))
            else:
                posts = Post.query.filter(Post.category == self)
        return posts


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10), unique=True)

    def __init__(self, content):
        self.content = content

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def posts_query(self, query=None):
        if query:
            posts = query.filter(Post.tags.contains(self))
        else:
            posts = self.posts
        return posts

    def posts_count(self, query=None):
        if query:
            count = query.filter(Post.tags.contains(self)).count()
        else:
            count = self.posts.count()
        return count