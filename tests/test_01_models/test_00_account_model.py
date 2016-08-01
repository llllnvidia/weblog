# -*- coding: utf-8 -*-
import unittest
import time
from datetime import datetime
from app import create_app, db
from app.models.account import User, AnonymousUser, Role, Permission, Follow
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        User.add_admin()
        User.add_test_user()
        User.add_admin_dialogue(1)
        User.add_self_follows()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_00_password_setter(self):
        u = User(username='john', password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_01_no_password_getter(self):
        u = User(username='john', password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_02_password_verification(self):
        u = User(username='john', password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_03_password_salts_are_random(self):
        u = User(username='john', password='cat')
        u2 = User(username='jack', password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_04_valid_confirmation_token(self):
        u = User(username='john', password='cat')
        u.save()
        token = u.generate_confirmation_token('something_need_confirm')
        self.assertTrue(u.confirm(token, 'something_need_confirm'))

    def test_05_invalid_confirmation_token(self):
        u1 = User(username='john', password='cat')
        u2 = User(username='jack', password='dog')
        u1.save()
        u2.save()
        token = u1.generate_confirmation_token('something_need_confirm')
        self.assertFalse(u2.confirm(token, 'something_need_confirm'))

    def test_06_expired_confirmation_token(self):
        u = User(username='john', password='cat')
        u.save()
        token = u.generate_confirmation_token('something_need_confirm', 1)
        time.sleep(2)
        self.assertFalse(u.confirm(token, 'something_need_confirm'))

    def test_07_valid_reset_token(self):
        u = User(username='john', password='cat')
        u.save()
        token = u.generate_confirmation_token('reset_password')
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_08_invalid_reset_token(self):
        u1 = User(username='john', password='cat')
        u2 = User(username='jack', password='dog')
        u1.save()
        u2.save()
        token = u1.generate_confirmation_token('reset_password')
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_09_roles_and_permissions(self):
        u = User(username='john', email='john@example.com', password='cat')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_10_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.is_administrator())
        self.assertFalse(u.is_authenticated)
        self.assertTrue(u.is_anonymous)
        self.assertFalse(u.is_moderator())

    def test_11_timestamps(self):
        u = User(username='john', password='cat')
        u.save()
        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 5)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 5)

    def test_12_ping(self):
        u = User(username='john', password='cat')
        u.save()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_13_follows(self):
        u1 = User(username='john', email='john@example.com', password='cat')
        u2 = User(username='susan', email='susan@example.org', password='dog')
        u1.save()
        u2.save()
        self.assertFalse(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        timestamp_before = datetime.utcnow()
        u1.follow(u2)
        timestamp_after = datetime.utcnow()
        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u1.is_followed_by(u2))
        self.assertTrue(u2.is_followed_by(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u2.followers.count() == 2)
        f = u1.followed.all()[-1]
        self.assertTrue(f.followed == u2)
        self.assertTrue(timestamp_before <= f.timestamp <= timestamp_after)
        f = u2.followers.all()[-1]
        self.assertTrue(f.follower == u1)
        u1.not_follow(u2)
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 4)
        u2.follow(u1)
        u2.delete()
        self.assertTrue(Follow.query.count() == 3)

    def test_14_role_and_user_repr(self):
        u = User(username='john', email='john@example.com', password='cat')
        self.assertTrue("<Role u'User'>" == u.role.__repr__())
        self.assertTrue("<User john ID 3>" == u.__repr__())

    def test_15_role_delete(self):
        roles = Role.query.all()
        for role in roles:
            role.delete()
        self.assertTrue(Role.query.count() == 0)

    def test_16_user_delete(self):
        users = User.query.all()
        from app.models.post import Post, Comment
        from app.models.message import Chat
        for x in range(2):
            post_new = Post(author=users[x])
            post_new.save()
            comment_new = Comment(author=users[x])
            comment_new.save()
            users[x].get_message_from_admin(content='User', link_id=users[x].id, link_type='user')
        self.assertTrue(User.query.count() == 2)
        self.assertTrue(Post.query.count() == 2)
        self.assertTrue(Comment.query.count() == 2)
        self.assertTrue(Chat.query.count() == 2)
        for user in users:
            user.delete()
        self.assertTrue(User.query.count() == 0)
        self.assertTrue(Post.query.count() == 0)
        self.assertTrue(Comment.query.count() == 0)
        self.assertTrue(Chat.query.count() == 0)

    def test_17_get_followed_posts(self):
        user = User.query.first()
        self.assertTrue(user.followed_posts.count() == 0)
        from app.models.post import Post
        post = Post(body='Post is editing!', author=user)
        post.save()
        self.assertTrue(user.followed_posts.count() == 1)
        tester = User.query.get(2)
        tester.follow(user)
        self.assertTrue(tester.followed_posts.count() == 1)

    def test_18_get_message_from_admin(self):
        user = User.query.filter_by(username='tester').first()
        from app.models.post import Post
        post = Post(body='Post is editing!', author=user)
        post.save()
        user.get_message_from_admin(content='User', link_id=user.id, link_type='user')
        user.get_message_from_admin(content='Comment', link_id=post.id, link_type='comment')
        user.get_message_from_admin(content='Post', link_id=post.id, link_type='post')
        user.get_message_from_admin(content='None')
        self.assertTrue(user.dialogues.count() == 1)
        self.assertTrue(user.dialogues.first().chats.count() == 4)
        admin = User.query.first()
        self.assertTrue(admin.dialogues.count() == 1)
        self.assertTrue(admin.dialogues.first().chats.count() == 4)
        admin_second = User(username='john', role=Role.query.filter_by(name='Administrator').first())
        admin_second.save()
        admin.get_message_from_admin(content='User', link_id=user.id, link_type='user')
        admin.get_message_from_admin(content='Comment', link_id=post.id, link_type='comment')
        admin.get_message_from_admin(content='Post', link_id=post.id, link_type='post')
        admin.get_message_from_admin(content='None')
        self.assertTrue(admin.dialogues.count() == 2)
        from app.models.message import Dialogue
        self.assertTrue(Dialogue.get_dialogue(admin, admin_second).chats.count() == 4)
        self.assertTrue(Dialogue.get_dialogue(admin, user).chats.count() == 4)
        self.assertTrue(admin_second.dialogues.first().chats.count() == 4)

    def test_19_add_self_follows(self):
        user = User.query.filter_by(username='tester').first()
        user.not_follow(user)
        self.assertTrue(user.followers.count() == 0)
        User.add_self_follows()
        self.assertTrue(user.followers.count() == 1)
        self.assertTrue(user.is_following(user))

if __name__ == '__main__':
    unittest.main()
