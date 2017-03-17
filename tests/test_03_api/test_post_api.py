# -*- coding:utf-8 -*-
import unittest
import json
from math import ceil
from random import choice
from elizabeth import Text, Personal
from werkzeug.exceptions import BadRequest

from app import create_app, db
from app.models.account import User
from app.models.post import Post, Category, Tag
from app.rest.post.parsers import parser_post_post
from tests.dummydata import (basic_deploy, generate_user, generate_tag,
                             generate_category, generate_post)


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
            return post

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
        data = dict(title=title, summary=summary, body=body)
        response = self.client.post(
            "/api/post",
            data=json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 401)

        self.login()
        response = self.client.post(
            "/api/post",
            data=json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 201)

        post = Post.query.filter_by(title=title).first()
        self.assertIsNotNone(post)

        data = json.loads(response.data)["next"]
        post_id = data.split("/")[-1]
        self.assertEqual(post.id, int(post_id))
        self.assertEqual(post.body, body)
        self.assertEqual(post.summary, summary)
        self.assertEqual(post.author, self.data["user"])

    def test_02_category_check(self):
        self.login()
        title = self.text.title()
        summary = self.text.text(3)
        body = self.text.text(6)
        category = self.text.word()
        data = dict(title=title, summary=summary, body=body, category=category)
        with self.app.test_request_context(
                "/api/post",
                method="post",
                data=json.dumps(data),
                content_type="application/json"):
            with self.assertRaises(BadRequest):
                parser_post_post.parse_args()

            category = Category(name=category)
            category.save()
            args = parser_post_post.parse_args()
            self.assertEqual(category, args.get("category"))

    def test_03_tag_parser(self):
        self.login()
        title = self.text.title()
        summary = self.text.text(3)
        body = self.text.text(6)
        tag = ",".join(self.text.word() for _ in range(3))
        data = dict(title=title, summary=summary, body=body, tag=tag)
        with self.app.test_request_context(
                "/api/post",
                method="post",
                data=json.dumps(data),
                content_type="application/json") as request:
            with self.assertRaises(BadRequest):
                parser_post_post.parse_args()
                response = request.process_response()
                data = json.loads(response.data)
                self.assertEqual(
                    data["message"]["tag"],
                    r"""Tag sound format like 'A','B' or "A", "B" """)

        data["tag"] = ','.join("'" + self.text.word() + "'" for _ in range(3))
        with self.app.test_request_context(
                "/api/post",
                method="post",
                data=json.dumps(data),
                content_type="application/json"):
            args = parser_post_post.parse_args()
            tag_ = ",".join("'" + tag + "'" for tag in args.get("tags"))
            self.assertEqual(tag_, data["tag"])

    def test_04_post_put(self):
        self.login()
        post = self.new_post()

        title = self.text.title()
        summary = self.text.text(3)
        body = self.text.text(6)
        category = self.text.word()
        Category(name=category).save()
        tag = ",".join("'" + self.text.word() + "'" for _ in range(3))
        data = dict(
            title=title,
            summary=summary,
            body=body,
            category=category,
            tag=tag)
        self.assertEqual(len(post.tags), 1)

        response = self.client.put(
            "/api/post/1",
            data=json.dumps(data),
            content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.title, title)
        self.assertEqual(post.summary, summary)
        self.assertEqual(post.body, body)
        self.assertEqual(post.category.name, category)
        self.assertEqual(len(post.tags), 3)

    def test_05_post_delete(self):
        self.new_post()
        self.assertEqual(Post.query.count(), 1)

        response = self.client.delete("/api/post/1")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Post.query.count(), 1)

        self.login()
        response = self.client.delete("/api/post/1")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Post.query.count(), 0)

    def test_06_post_get(self):
        basic_deploy()
        generate_user()
        generate_tag()
        generate_category()
        generate_post()
        self.assertNotEqual(Post.query.count(), 0)

        authors = User.query.all()
        tags = Tag.query.all()
        categories = Category.query.all()
        page_size = self.app.config.get("POSTS_PER_PAGE", 10)

        def asserts():
            self.assertEqual(page_size
                             if post_count >= page_size else post_count,
                             len(data["post"]))
            self.assertEqual(ceil(post_count / page_size), data["pagesize"])

        author = choice(authors)
        response = self.client.get(
            "/api/post", query_string=dict(author=author.username))
        data = json.loads(response.data)
        post_count = author.posts.count()
        asserts()

        tag = choice(tags)
        response = self.client.get(
            "/api/post", query_string=dict(tag="'" + tag.name + "'"))
        data = json.loads(response.data)
        post_count = tag.posts.count()
        asserts()

        category = choice(categories)
        response = self.client.get(
            "/api/post", query_string=dict(category=category.name))
        data = json.loads(response.data)
        post_count = category.posts.count()
        asserts()

        tags.remove(tag)
        tag_two = choice(tags)
        response = self.client.get(
            "/api/post",
            query_string=dict(tag=",".join("'" + t.name + "'"
                                           for t in [tag, tag_two])))
        data = json.loads(response.data)
        post_count = tag.posts_count(tag_two.posts)
        asserts()

        response = self.client.get(
            "/api/post",
            query_string=dict(
                author=author.username, tag="'" + tag.name + "'"))
        data = json.loads(response.data)
        post_count = tag.posts_count(author.posts)
        asserts()

        response = self.client.get(
            "/api/post",
            query_string=dict(author=author.username, category=category.name))
        data = json.loads(response.data)
        post_count = category.posts_count(author.posts)
        asserts()

        response = self.client.get(
            "/api/post",
            query_string=dict(
                category=category.name, tag="'" + tag.name + "'"))
        data = json.loads(response.data)
        post_count = category.posts_count(tag.posts)
        asserts()

        response = self.client.get(
            "/api/post",
            query_string=dict(
                author=author.username,
                tag="'" + tag.name + "'",
                category=category.name))
        data = json.loads(response.data)
        post_count = category.posts_count(tag.posts_query(author.posts))
        asserts()


if __name__ == "__main__":
    unittest.main()
