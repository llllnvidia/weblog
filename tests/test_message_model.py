# -*- coding: utf-8 -*-
import unittest
from app import create_app, db
from app.models.account import User, Role
from app.models.message import Dialogue, Gallery, Chat


class MessageModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        User.add_admin()
        User.add_test_user()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_00_dialogue_save_and_delete(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        self.assertTrue(dialogue.galleries.count() == 2)
        self.assertTrue(Dialogue.query.count() == 1)
        dialogue.delete()
        self.assertTrue(Dialogue.query.count() == 0)

    def test_01_gallery_save_repr_and_delete(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        self.assertTrue(dialogue.galleries.count() == 2)
        gallery = dialogue.get_gallery(admin)
        self.assertTrue(gallery.__repr__() == '<Dialogue 1 User Admin>')
        gallery.delete()
        self.assertTrue(dialogue.galleries.count() == 1)
