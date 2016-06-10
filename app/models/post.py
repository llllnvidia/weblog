# -*- coding: utf-8 -*-
from datetime import datetime

from app import db

posttags = db.Table('posttags',
                    db.Column('tags_id', db.Integer, db.ForeignKey('tags.id')),
                    db.Column('posts_id', db.Integer, db.ForeignKey('posts.id'))
                    )


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_article = db.Column(db.Boolean, default=False)
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    title = db.Column(db.Text)
    summary = db.Column(db.Text)
    last_edit = db.Column(db.DateTime)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category',
                               foreign_keys=[category_id],
                               backref=db.backref('posts', lazy='dynamic'))
    tags = db.relationship('Tag',
                           secondary=posttags,
                           backref=db.backref('posts', lazy='dynamic'))

    def __repr__(self):
        if self.title:
            return '<Post %s Author %s>' % (self.title, self.author.username)
        else:
            return '<Post %d Author %s>' % (self.id, self.author.username)

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
        if not self.is_tagging(tag):
            self.tags.append(tag)

    def not_tag(self, tag):
        if self.is_tagging(tag):
            self.tags.remove(tag)

    def is_tagging(self, tag):
        return tag in self.tags


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    parent_category = db.relationship('Category', uselist=False, remote_side=[id],
                                      backref=db.backref('son_categories', uselist=True))

    def __init__(self, name, parent_category=None):
        self.name = name
        self.parent_category = parent_category

    def __repr__(self):
        name = None
        if self.parent_category:
            name = Category.query.filter_by(id=self.parent_id).first().name
        return '<Category %s Parent %s Son %s>' % (self.name,
                                                   name,
                                                   [cg.name for cg in self.son_categories])

    @staticmethod
    def add_none():
        none = Category(name=u'None')
        none.save()
        for post in Post.query.all():
            if post.category is None:
                post.category = none
                post.save()

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
            sum_posts_count = 0
            for category in self.son_categories:
                sum_posts_count = sum_posts_count + query.filter(Post.category == category).count()
        else:
            count = self.posts.count()
            sum_posts_count = 0
            for category in self.son_categories:
                sum_posts_count = sum_posts_count + category.posts_count()
        count = count + sum_posts_count
        return count

    def posts_query(self, query=None):
        if query:
            posts = query.filter(Post.category == self)
            if self.son_categories:
                for son_category in self.son_categories:
                    posts = posts.union(query.filter(Post.category == son_category))
        else:
            posts = Post.query.filter(Post.category == self)
            if self.son_categories:
                for son_category in self.son_categories:
                    posts = posts.union(Post.query.filter(Post.category == son_category))
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
