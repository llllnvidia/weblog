from datetime import datetime

from app import db


class Dialogue(db.Model):
    __tablename__ = 'dialogues'
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    invited_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                        primary_key=True)
    show = db.Column(db.Boolean, default=True, index=True)
    count = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())
    chats = db.relationship('Chat', backref='dialogue', lazy='dynamic')

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def not_show_itself(self):
        self.show = False
        self.save()

    def show_itself(self):
        self.show = True
        self.save()

    def has_new_chats(self):
        if self.count < self.messages.count():
            return True
        else:
            return False

    def update_chats(self):
        self.count = self.messages.count()
        self.timestamp = datetime.utcnow()
        self.save()

    def new_chat(self, *args):
        chat = Chat(*args)
        chat.appointment = self
        chat.save()


class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('dialogues.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    context = db.Column(db.Text)
    link_comment = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow())

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
