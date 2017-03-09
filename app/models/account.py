# -*- coding: utf-8 -*-
from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager
from app.models.message import Dialogue, Session


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @staticmethod
    def insert_roles():
        roles = {
            "User": (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            "Moderator": (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            "Administrator": (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            role.save()


class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_ARTICLES = 0x04
    MODERATE_COMMENTS = 0x08
    ADMINISTER = 0x80


class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all,delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all,delete-orphan')
    chats = db.relationship('Chat', backref='author', lazy='dynamic')
    sessions = db.relationship('Session',
                                foreign_keys=[Session.user_id],
                                backref=db.backref('user', lazy='joined'),
                                lazy='dynamic',
                                cascade='all,delete-orphan')
    new_messages_count = db.Column(db.Integer)

    def __repr__(self):
        return '<User %s ID %d>' % (self.username, self.id)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()
        self.save()
        self.follow(self)
        self.save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        for comment_delete in self.comments:
            comment_delete.delete()
        for chat_delete in self.chats:
            chat_delete.delete()
        for post_delete in self.posts:
            post_delete.delete()
        for session_delete in self.sessions:
            session_delete.delete()
        db.session.delete(self)
        db.session.commit()

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(0xff)

    def is_moderator(self):
        return self.can(0x0f)

    def ping(self):
        self.new_messages_count = 0
        self.last_seen = datetime.utcnow()
        for session in self.sessions:
            self.new_messages_count = self.new_messages_count + session.having_new_chats
        self.save()

    @property
    def password(self):
        raise AttributeError('密码不可用,只可用于赋值。')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, confirm_type, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({confirm_type: self.id})

    def confirm(self, token, confirm_type):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (AttributeError, BadSignature):
            return False
        if data.get(confirm_type) != self.id:
            return False
        return True

    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            f.save()

    def not_follow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            f.delete()

    def is_following(self, user):
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        from app.models.post import Post
        return Post.query.join(Follow, Follow.followed_id == Post.author_id) \
            .filter(Follow.follower_id == self.id)

    @property
    def dialogues(self):
        return Dialogue.query.join(Session, Session.dialogue_id == Dialogue.id) \
            .filter(Session.user_id == self.id)

    @property
    def gravatar(self, size=100, default="identicon", rating="g"):
        from flask import request
        from hashlib import md5
        if request.is_secure:
            url = "https://secure.gravatar.com/avatar"
        else:
            url = "http://www.gravatar.com/avatar"
        hash_ = md5(self.email.encode("utf-8")).hexdigest()
        return f"{url}/{hash_}?s={size}&d={default}&r={rating}"



class AnonymousUser(AnonymousUserMixin):

    def can(self, permissions):
        return False

    def is_moderator(self):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
