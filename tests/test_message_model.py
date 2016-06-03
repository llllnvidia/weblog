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

    def test_02_gallery_update_name(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        gallery = dialogue.get_gallery(tester)
        self.assertTrue(gallery.name == '系统消息')
        gallery.update_name()
        self.assertTrue(gallery.name == 'Admin')
        gallery.update_name('Tester')
        self.assertTrue(gallery.name == 'Tester')

    def test_03_gallery_having_new_chats(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        gallery = dialogue.get_gallery(tester)
        self.assertTrue(gallery.having_new_chats == 0)
        dialogue.new_chat(author=admin, content='test')
        self.assertTrue(gallery.count == 0)
        self.assertTrue(gallery.having_new_chats == 1)

    def test_04_dialogue_init(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        dialogue.delete()
        self.assertTrue(Dialogue.query.count() == 0)
        self.assertTrue(Gallery.query.count() == 0)
        dialogue = Dialogue(admin, tester)
        self.assertTrue(Dialogue.query.count() == 1)
        self.assertTrue(Gallery.query.count() == 2)
        dialogue.delete()
        self.assertTrue(Dialogue.query.count() == 0)
        self.assertTrue(Gallery.query.count() == 0)
        dialogue = Dialogue(admin, tester, 'test')
        self.assertTrue(Dialogue.query.count() == 1)
        self.assertTrue(Gallery.query.count() == 2)
        gallery = dialogue.get_gallery(tester)
        self.assertTrue(gallery.name == 'test')
        dialogue.delete()
        self.assertTrue(Dialogue.query.count() == 0)
        self.assertTrue(Gallery.query.count() == 0)
        Dialogue(admin)
        self.assertTrue(Dialogue.query.count() == 0)
        self.assertTrue(Gallery.query.count() == 0)

    def test_05_dialogue_update_show(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        gallery = dialogue.get_gallery(admin)
        gallery.show = False
        dialogue.update_show()
        self.assertTrue(gallery.show)

    def test_06_dialogue_update_chats(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        gallery = dialogue.get_gallery(admin)
        gallery.delete()
        self.assertTrue(Gallery.query.count() == 1)
        dialogue.update_chats(admin)
        self.assertTrue(Gallery.query.count() == 2)
        gallery = dialogue.get_gallery(tester)
        self.assertTrue(gallery.count == 0)
        dialogue.new_chat(author=admin, content='test')
        dialogue.update_chats(tester)
        self.assertTrue(gallery.count == 1)

    def test_07_dialogue_having_new_chats(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        self.assertTrue(dialogue.having_new_chats(tester) == 0)
        self.assertTrue(dialogue.having_new_chats(admin) == 0)
        dialogue.new_chat(author=admin, content='test')
        self.assertTrue(dialogue.having_new_chats(tester) == 1)
        self.assertTrue(dialogue.having_new_chats(admin) == 0)
        gallery = dialogue.get_gallery(admin)
        gallery.delete()
        self.assertTrue(dialogue.having_new_chats(admin) == 0)

    def test_08_dialogue_is_together(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        user = User(username='tester2')
        user.save()
        dialogue = Dialogue.get_dialogue(admin, tester)
        self.assertTrue(Dialogue.is_together(admin, tester))
        self.assertTrue(Dialogue.is_together(tester, admin))
        dialogue.delete()
        self.assertFalse(Dialogue.is_together(admin, tester))
        self.assertFalse(Dialogue.is_together(tester, admin))

    def test_09_chat_save_and_delete(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        self.assertTrue(Chat.query.count() == 0)
        chat = Chat(author=admin, dialogue=dialogue, content='test',
                    link_id=1, link_type='test')
        chat.save()
        self.assertTrue(Chat.query.count() == 1)
        chat.delete()
        self.assertTrue(Chat.query.count() == 0)

    def test_10_dialogue_name(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        gallery = dialogue.get_gallery(tester)
        self.assertTrue(dialogue.name(tester) == gallery.name)

    def test_11_dialogue_leave(self):
        admin = User.query.filter_by(username='Admin').first()
        tester = User.query.filter_by(username='tester').first()
        dialogue = Dialogue.get_dialogue(admin, tester)
        self.assertTrue(dialogue.galleries.count() == 2)
        dialogue.user_leave(admin)
        self.assertTrue(dialogue.galleries.count() == 1)
