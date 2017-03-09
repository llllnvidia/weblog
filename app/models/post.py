# -*- coding: utf-8 -*-
from datetime import datetime

from app import db

post_tag = db.Table('post_tag',
                    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id')),
                    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'))
                    )


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    is_draft = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.Text)
    summary = db.Column(db.Text)
    last_edit = db.Column(db.DateTime)
    count = db.Column(db.BigInteger, default=0, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    category = db.relationship('Category',
                               foreign_keys=[category_id],
                               backref=db.backref('posts', lazy='dynamic'))
    tags = db.relationship('Tag',
                           secondary=post_tag,
                           backref=db.backref('posts', lazy='dynamic'))

    def __repr__(self):
        return '<Post %s Author %s>' % (self.title, self.author.username)

    def ping(self):
        self.last_edit = datetime.utcnow()
        self.save()

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


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    parent = db.relationship('Category', uselist=False, remote_side=[id],
                             backref=db.backref('children', uselist=True))

    def __repr__(self):
        name = self.name
        parent_name = self.parent.name
        sons_name = ",".join([cg.name for cg in self.son_categories])
        return f"<Category {name} Parent {parent_name} Son {sons_name}>"

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        for post in self.posts:
            post.category_id = None
            post.save()
        db.session.delete(self)
        db.session.commit()

    def posts_count(self, query=None):
        if query:
            count = query.filter(Post.category == self).count()
            sum_posts_count = 0
            for child in self.children:
                sum_posts_count = sum_posts_count + query.filter(Post.category == child).count()
        else:
            count = self.posts.count()
            sum_posts_count = 0
            for child in self.children:
                sum_posts_count = sum_posts_count + child.posts_count()
        count += sum_posts_count
        return count

    def posts_query(self, query=None):
        if query:
            posts = query.filter(Post.category == self)
            if self.children:
                for child in self.children:
                    posts = posts.union(query.filter(Post.category == child))
        else:
            posts = Post.query.filter(Post.category == self)
            if self.children:
                for child in self.children:
                    posts = posts.union(Post.query.filter(Post.category == child))
        return posts


class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)

    def __repr__(self):
        return "<Tag {}>".format(self.name)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        for post_need_changed in self.posts:
            post_need_changed.tags.remove(self)
            post_need_changed.save()
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
