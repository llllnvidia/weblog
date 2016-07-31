from datetime import datetime

from app import db


class Session(db.Model):
    __tablename__ = 'sessions'
    id = db.Column(db.Integer, primary_key=True)
    dialogue_id = db.Column(db.Integer, db.ForeignKey('dialogues.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String)
    count = db.Column(db.Integer, default=0)
    show = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __init__(self, dialogue, user, name=None):
        self.dialogue = dialogue
        self.user = user
        if name:
            self.name = name
        else:
            self.name = self.get_temporary_name

    def __repr__(self):
        return '<Dialogue %s User %s>' % (self.dialogue.id, self.user.username)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def update_name(self, name=None):
        if name:
            self.name = name
        else:
            self.name = self.get_temporary_name
        self.save()

    @property
    def get_temporary_name(self):
        users = []
        dialogue = self.dialogue
        for session in dialogue.sessions:
            if session.id != self.id:
                users.append(session.user.username)
        return ' '.join(users)

    @property
    def having_new_chats(self):
        if self.dialogue.chats.count() > self.count:
            return self.dialogue.chats.count() - self.count
        else:
            return 0


class Dialogue(db.Model):
    __tablename__ = 'dialogues'
    id = db.Column(db.Integer, primary_key=True)
    sessions = db.relationship('Session',
                               foreign_keys=[Session.dialogue_id],
                               backref=db.backref('dialogue', lazy='joined'),
                               lazy='dynamic',
                               cascade='all,delete-orphan')
    chats = db.relationship('Chat', backref='dialogue', lazy='dynamic')

    def __init__(self, user=None, user_has_name=None, name=None):
        if name and user_has_name and user:
            if not Dialogue.is_together(user_has_name, user):
                self.save()
                self.user_join(user_has_name, name)
                self.user_join(user)
        elif user_has_name and user:
            if not Dialogue.is_together(user_has_name, user):
                self.save()
                self.user_join(user)
                self.user_join(user_has_name)
                for session in self.sessions:
                    session.update_name()
        else:
            pass

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        for session in self.sessions:
            session.delete()
        for chat in self.chats:
            chat.delete()
        db.session.delete(self)
        db.session.commit()

    def update_show(self):
        for session in self.sessions:
            session.show = True
            session.save()

    def name(self, user):
        if self.is_joining(user):
            session = self.sessions.filter_by(user_id=user.id).first()
            return session.name

    def user_join(self, user, name=None):
        if not self.is_joining(user):
            if name:
                session = Session(dialogue=self, user=user, name=name)
            else:
                session = Session(dialogue=self, user=user)
            session.count = self.chats.count()
            session.save()

    def user_leave(self, user):
        if self.is_joining(user):
            session = self.sessions.filter_by(user_id=user.id).first()
            session.delete()

    def is_joining(self, user):
        if self.sessions.filter_by(user=user).first():
            return True
        else:
            return False

    def get_session(self, user):
        return self.sessions.filter_by(user_id=user.id).first()

    def update_chats(self, user):
        if self.is_joining(user):
            session = self.sessions.filter_by(user_id=user.id).first()
            session.count = self.chats.count()
            session.timestamp = datetime.utcnow()
            session.save()
        else:
            self.user_join(user)

    def having_new_chats(self, user):
        if self.is_joining(user):
            session = self.sessions.filter_by(user_id=user.id).first()
            return session.having_new_chats
        else:
            return 0

    @staticmethod
    def is_together(user_a, user_b):
        dialogues_a = user_a.dialogues
        dialogues_b = user_b.dialogues
        if dialogues_a.count() and dialogues_b.count():
            if dialogues_a.count() > dialogues_b.count():
                for dialogue in dialogues_b:
                    if dialogue.is_joining(user_a):
                        return True
            else:
                for dialogue in dialogues_a:
                    if dialogue.is_joining(user_b):
                        return True
        return False

    @staticmethod
    def get_dialogue(user_a, user_b):
        dialogues_a = user_a.dialogues
        dialogues_b = user_b.dialogues
        if dialogues_a.count() and dialogues_b.count():
            if dialogues_a.count() > dialogues_b.count():
                for dialogue in dialogues_b:
                    if dialogue.is_joining(user_a):
                        return dialogue
            else:
                for dialogue in dialogues_a:
                    if dialogue.is_joining(user_b):
                        return dialogue

    def new_chat(self, author, content, **kwargs):
        chat = Chat(dialogue=self, author=author, content=content, **kwargs)
        self.update_chats(author)
        self.update_show()
        chat.save()


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dialogue_id = db.Column(db.Integer, db.ForeignKey('dialogues.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text)
    link = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __init__(self, dialogue, author, content, link_id=None, link_type=None):
        self.dialogue = dialogue
        self.author = author
        self.content = content
        if link_id:
            from flask import url_for
            if link_type == 'comment':
                self.link = url_for('post.article', post_id=link_id) + '#comments'
            elif link_type == 'user':
                self.link = url_for('main.user', username=link_id)
            elif link_type == 'post':
                self.link = url_for('post.article', post_id=link_id)

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
