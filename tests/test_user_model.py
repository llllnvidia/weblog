# -*- coding: utf-8 -*-
import unittest
import time
from datetime import datetime
from app import create_app, db
from app.models.account import User, AnonymousUser, Role, Permission, Follow


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_00_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_01_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_02_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_03_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_04_valid_confirmation_token(self):
        u = User(password='cat')
        u.save()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    def test_05_invalid_confirmation_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        u1.save()
        u2.save()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    def test_06_expired_confirmation_token(self):
        u = User(password='cat')
        u.save()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    def test_07_valid_reset_token(self):
        u = User(password='cat')
        u.save()
        token = u.generate_reset_token()
        self.assertTrue(u.reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    def test_08_invalid_reset_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        u1.save()
        u2.save()
        token = u1.generate_reset_token()
        self.assertFalse(u2.reset_password(token, 'horse'))
        self.assertTrue(u2.verify_password('dog'))

    def test_09_roles_and_permissions(self):
        u = User(email='john@example.com', password='cat')
        self.assertTrue(u.can(Permission.WRITE_ARTICLES))
        self.assertFalse(u.can(Permission.MODERATE_COMMENTS))

    def test_10_anonymous_user(self):
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))

    def test_11_timestamps(self):
        u = User(password='cat')
        u.save()
        self.assertTrue(
            (datetime.utcnow() - u.member_since).total_seconds() < 5)
        self.assertTrue(
            (datetime.utcnow() - u.last_seen).total_seconds() < 5)

    def test_12_ping(self):
        u = User(password='cat')
        u.save()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_13_follows(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
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
        u1.unfollow(u2)
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 1)
        self.assertTrue(Follow.query.count() == 2)
        u2.follow(u1)
        u2.delete()
        self.assertTrue(Follow.query.count() == 1)
