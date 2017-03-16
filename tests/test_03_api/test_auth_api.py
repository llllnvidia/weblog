# -*- coding:utf-8 -*-
import unittest
import json
from time import sleep
from elizabeth import Personal
from werkzeug.http import parse_cookie

from app import create_app, db
from app.models.account import User


class AuthApiTestCase(unittest.TestCase):
    person = Personal()

    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        kwargs = {
            "username": self.person.username(),
            "email": self.person.email(),
            "password": self.person.password(16)
        }
        user = User(**kwargs)
        user.save()
        del kwargs["email"]
        self.data = {"kwargs": kwargs, "user": user}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_01_post_method(self):
        kwargs = self.data["kwargs"]
        user = self.data["user"]
        kwargs_fake = dict(
            username=self.person.username(), password=self.person.password(16))
        response = self.client.post(
            "/api/auth",
            data=json.dumps(kwargs_fake),
            content_type="application/json")
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.data)
        self.assertEqual(data["message"]["username"],
                         "valid username is required for authentication")

        response = self.client.post(
            "/api/auth",
            data=json.dumps(kwargs),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.data)
        self.assertEqual(User.confirm("login", data["token"]).id, user.id)

        kwargs["password"] = self.person.password(16)
        response = self.client.post(
            "/api/auth",
            data=json.dumps(kwargs),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)

        data = json.loads(response.data)
        self.assertEqual(data["message"], "invalid username or password")

    def test_02_refresh_token(self):
        kwargs = self.data["kwargs"]
        user = self.data["user"]

        token_fake = json.dumps(dict(token=json.dumps(kwargs)))
        response = self.client.get(
            "/api/auth", query_string=dict(token=token_fake))
        self.assertEqual(response.status_code, 401)

        response = self.client.post(
            "/api/auth",
            data=json.dumps(kwargs),
            content_type="application/json")
        token_1 = parse_cookie(
            response.headers.getlist('Set-Cookie')[0])["token"]
        sleep(1)
        response = self.client.get(
            "/api/auth", query_string=dict(token=token_1))
        token_2 = parse_cookie(
            response.headers.getlist("Set-Cookie")[0])["token"]
        self.assertNotEqual(token_1, token_2)
        self.assertEqual(User.confirm("login", token_1).id, user.id)
        self.assertEqual(User.confirm("login", token_2).id, user.id)


if __name__ == "__main__":
    unittest.main()
