# -*- coding:utf-8 -*-
import unittest
import json
from elizabeth import Text, Personal

from app import create_app, db
from app.models.account import User
from app.models.post import Post, Category, Tag


class PostApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        person = Personal()
        text = Text()
        kwargs = {
            "username": person.username(),
            "email": person.email(),
            "password": person.password(16)
        }
        user = User(**kwargs)
        user.save()

        def __auth():
            response = self.client.post(
                "/api/auth",
                data=json.dumps(kwargs),
                content_type="application/json")
            self.assertEqual(response.status_code, 200)

        def __post():
            post = Post(
                title=self.text.title(),
                summary=text.text(3),
                body=text.text(6),
                author=user)
            category = Category(name=text.word())
            category.save()
            post.category = category
            tag = Tag(name=text.word())
            tag.save()
            post.tags.append(tag)
            post.save()

        self.login = __auth
        self.new_post = __post
        del kwargs["email"]
        self.data = {"kwargs": kwargs, "user": user}
        self.text = text
        self.person = person

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_01_post_post(self):
        title = self.text.title()
        summary = self.text.text(3)
        body = self.text.text(6)
        tag = self.text.word()
        data = json.dumps(
            dict(title=title, summary=summary, body=body, tag=tag))
        response = self.client.post(
            "/api/post", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 401)

        self.login()
        response = self.client.post(
            "/api/post", data=data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        post = Post.query.filter_by(title=title).first()
        self.assertIsNotNone(post)

        data = json.loads(response.data)["next"]
        post_id = data.split("/")[-1]
        self.assertEqual(post.id, int(post_id))
        self.assertEqual(post.body, body)
        self.assertEqual(post.summary, summary)
        self.assertEqual(post.author, self.data["user"])
        self.assertEqual(post.tags[0].name, tag)

    def test_02_post_put(self):
        pass

    def test_03_post_delete(self):
        pass

    def test_04_post_create(self):
        pass


if __name__ == "__main__":
    unittest.main()
