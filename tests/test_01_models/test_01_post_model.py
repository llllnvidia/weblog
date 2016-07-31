# -*- coding: utf-8 -*-
import unittest
from datetime import datetime
from app import create_app, db
from app.models.account import User, Role
from app.models.post import Post, Category, Comment, Tag
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class PostModelTestCase(unittest.TestCase):
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

    def test_00_post_save_and_delete(self):
        post = Post(body='Post is editing!')
        post.save()
        comment = Comment(post=post)
        comment.save()
        self.assertTrue(Post.query.count() == 1)
        self.assertTrue(Comment.query.count() == 1)
        post.delete()
        self.assertTrue(Post.query.count() == 0)
        self.assertTrue(Comment.query.count() == 0)

    def test_01_post_repr(self):
        admin = User.query.get(1)
        post = Post(body='Post is editing!', author=admin, title='admin\'s post')
        post.save()
        self.assertTrue('<Post admin\'s post Author Admin>' == post.__repr__())

    def test_02_post_ping(self):
        post = Post(body='Post is editing!')
        post.save()
        before_timestamp = datetime.utcnow()
        post.ping()
        after_timestamp = datetime.utcnow()
        self.assertTrue(post.timestamp <= before_timestamp <= post.last_edit <= after_timestamp)

    def test_03_comment_save_and_delete(self):
        comment = Comment(body='Comment is Comment')
        comment.save()
        self.assertTrue(Comment.query.count() == 1)
        comment.delete()
        self.assertTrue(Comment.query.count() == 0)

    def test_04_category_repr_save_and_delete(self):
        self.assertTrue(Category.query.count() == 0)
        Category.add_none()
        category = Category(name='tester',
                            parent_category=Category.query.get(1))
        category.save()
        self.assertTrue('<Category tester Parent None Son []>' == category.__repr__())
        self.assertTrue(Category.query.count() == 2)
        post = Post(body='# Post Big title', category=category)
        post.save()
        self.assertTrue(category.posts.count() == 1)
        category.delete()
        self.assertTrue(Category.query.count() == 1)
        self.assertTrue(post.category_id == 1)

    def test_05_category_add_none(self):
        post = Post(body='# Post Big title')
        post.save()
        self.assertTrue(post.category is None)
        Category.add_none()
        self.assertTrue(post.category == Category.query.get(1))

    def test_06_category_posts_count(self):
        Category.add_none()
        none = Category.query.get(1)
        category = Category(name='tester',
                            parent_category=Category.query.get(1))
        category.save()
        self.assertTrue(none.posts_count() == 0)
        post = Post(body='# Post Big title', category=category)
        post.save()
        self.assertTrue(none.posts_count() == 1)
        self.assertTrue(category.posts_count() == 1)
        query = Post.query
        self.assertTrue(none.posts_count(query) == 1)
        self.assertTrue(category.posts_count(query) == 1)

    def test_07_category_posts_query(self):
        Category.add_none()
        none = Category.query.get(1)
        category = Category(name='tester',
                            parent_category=Category.query.get(1))
        category.save()
        self.assertTrue(none.posts_query().count() == 0)
        self.assertTrue(category.posts_query().count() == 0)
        post = Post(body='# Post Big title', category=category)
        post.save()
        query = Post.query
        self.assertTrue(none.posts_query().count() == 1)
        self.assertTrue(category.posts_query().count() == 1)
        self.assertTrue(none.posts_query(query).count() == 1)
        self.assertTrue(category.posts_query(query).count() == 1)

    def test_08_tag_save_and_delete(self):
        tag = Tag('test')
        self.assertTrue(Tag.query.count() == 0)
        tag.save()
        post = Post(tags=[tag])
        post.save()
        self.assertTrue(Tag.query.count() == 1)
        self.assertTrue(tag in post.tags)
        tag.delete()
        self.assertTrue(Tag.query.count() == 0)
        self.assertTrue(len(post.tags) == 0)

    def test_09_tag_and_post(self):
        tag = Tag('test')
        tag.save()
        post = Post(body='# Post Big title')
        post.save()
        self.assertTrue(post.tags == [])
        post.tag(tag)
        self.assertTrue(post.tags.pop() == tag)
        post.not_tag(tag)
        self.assertTrue(post.tags == [])

    def test_10_tag_posts_query_and_count(self):
        tag = Tag('test')
        tag.save()
        post = Post(body='# Post Big title')
        post.save()
        query = Post.query
        self.assertTrue(tag.posts_query().count() == 0)
        self.assertTrue(tag.posts_query(query).count() == 0)
        self.assertTrue(tag.posts_count() == 0)
        self.assertTrue(tag.posts_count(query) == 0)
        post.tag(tag)
        self.assertTrue(tag.posts_query().count() == 1)
        self.assertTrue(tag.posts_query(query).count() == 1)
        self.assertTrue(tag.posts_count() == 1)
        self.assertTrue(tag.posts_count(query) == 1)
        post.not_tag(tag)
        self.assertTrue(tag.posts_query().count() == 0)
        self.assertTrue(tag.posts_query(query).count() == 0)
        self.assertTrue(tag.posts_count() == 0)
        self.assertTrue(tag.posts_count(query) == 0)
