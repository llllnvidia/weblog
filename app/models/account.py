# -*- coding: utf-8 -*-
from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


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

    def __repr__(self):
        return "<User {} ID {}>".format(self.username, self.id)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
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
        raise AttributeError('password is unavailable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, confirm_type, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({confirm_type: self.id})

    @staticmethod
    def confirm(token, confirm_type):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (SignatureExpired, BadSignature):
            return None
        user_id = data.get(confirm_type, None)
        if (user_id):
            user = User.query.get(user_id)
            return user
        else:
            return None

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
