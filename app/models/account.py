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
            'User': (Permission.FOLLOW |
                     Permission.COMMENT |
                     Permission.WRITE_ARTICLES, True),
            'Moderator': (Permission.FOLLOW |
                          Permission.COMMENT |
                          Permission.WRITE_ARTICLES |
                          Permission.MODERATE_COMMENTS, False),
            'Administrator': (0xff, False)
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
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
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
        admin = User.query.filter_by(username=current_app.config['ADMIN']).first()
        if admin and admin != self:
            Dialogue(admin, self, name=u'系统消息')
        if not self.password_hash:
            self.password = u'123456'
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

    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                user.save()

    @staticmethod
    def add_admin():
        admin = User(email=u'Admin@weblog.com',
                     username=u'Admin',
                     password=u'1234',
                     confirmed=True,
                     member_since=datetime.utcnow())
        admin.role = Role.query.filter_by(name='Administrator').first()
        admin.save()

    @staticmethod
    def add_test_user():
        user = User(email=u'user@weblog.com',
                    username=u'tester',
                    password=u'1234',
                    confirmed=True,
                    member_since=datetime.utcnow())
        user.save()

    @staticmethod
    def add_admin_dialogue(id):
        for user in User.query.all():
            if user.id != id:
                Dialogue(User.query.get(id), user, name=u'系统消息')

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

    confirmed = db.Column(db.Boolean, default=False)

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

    def reset_password(self, token, new_password):
        if self.confirm(token, 'reset_password'):
            self.password = new_password
            self.save()
            return True
        else:
            return False

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

    def get_message_from_admin(self, content, link_id=None, link_type=None):
        admin = User.query.filter_by(username=current_app.config['ADMIN']).first()
        if not admin or self.id == admin.id :
            admin_list = User.query.filter_by(role=Role.query.filter_by(name='Administrator').first()).all()
            for admin_new in admin_list:
                if admin_new != admin:
                    admin = admin_new
                    break
        dialogue = Dialogue.get_dialogue(admin, self)
        if link_id and link_type:
            dialogue.new_chat(author=admin, content=content, link_id=link_id, link_type=link_type)
        else:
            dialogue.new_chat(author=admin, content=content)


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
