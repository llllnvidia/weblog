# -*- coding:utf-8 -*-
import unittest
from time import sleep
from elizabeth import Personal, Text


from app import create_app, db
from app.models.account import User


class ModelsAccountTestCase(unittest.TestCase):
    person = Personal()
    text = Text()

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_01_save_and_delete(self):
        kwargs = {"username": self.person.name(),
                  "email": self.person.email()}
        self.assertEqual(User.query.count(), 0)
        user = User(**kwargs)
        user.save()
        self.assertEqual(user.__repr__(), "<User {} ID {}>".format(kwargs["username"], 1))
        self.assertEqual(User.query.count(), 1)
        user.delete()
        self.assertEqual(User.query.count(), 0)

    def test_02_password(self):
        kwargs = {"username": self.person.name(),
                  "email": self.person.email()}
        password = self.person.password(16)
        user = User(**kwargs)
        self.assertIsNone(user.password_hash)
        with self.assertRaises(AttributeError):
            _ = user.password
        user.password = password
        self.assertIsNotNone(user.password_hash)
        self.assertTrue(user.verify_password(password))
        self.assertFalse(user.verify_password(self.person.password(16)))

    def test_03_token(self):
        kwargs = {"username": self.person.name(),
                  "email": self.person.email()}
        key_1, key_2 = self.text.words(2)
        user = User(**kwargs)
        user.save()
        token_1 = user.generate_token(key_1)
        sleep(1)
        token_1_delay = user.generate_token(key_1)
        self.assertNotEqual(token_1, token_1_delay)
        token_2 = user.generate_token(key_2)
        self.assertEquals((User.confirm(key_1, token_1), user),
                          (User.confirm(key_2, token_2), user))
        self.assertIsNone(User.confirm(key_2, token_1))
        token = user.generate_token(key_1, expiration=2)
        self.assertEqual(User.confirm(key_1, token), user)
        sleep(3)
        self.assertIsNone(User.confirm(key_1, token))


if __name__ == "__main__":
    unittest.main()