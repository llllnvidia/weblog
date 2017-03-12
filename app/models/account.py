# -*- coding: utf-8 -*-
from datetime import datetime

from flask import current_app
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return "<User {} ID {}>".format(self.username, self.id)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        for post_delete in self.posts:
            post_delete.delete()
        db.session.delete(self)
        db.session.commit()

    def ping(self):
        self.last_seen = datetime.utcnow()
        self.save()

    @property
    def password(self):
        raise AttributeError('password is unavailable')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, key, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({key: self.id}).decode("utf-8")

    @staticmethod
    def confirm(key, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except (SignatureExpired, BadSignature):
            return None

        user_id = data.get(key)
        if user_id:
            user = User.query.get(user_id)
            if user:
                return user

        return None

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
