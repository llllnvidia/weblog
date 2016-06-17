# -*- coding: utf-8 -*-
import re
import unittest
from flask import url_for
from app import create_app, db
from app.models.account import User, Role
from app.models.post import Post, Category, Tag, Comment
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class FlaskClientTestCase00(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_00_home_page(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue('CodeBlog' in response.data)

    def test_01_register(self):
        # register a new account
        response = self.client.get(url_for('auth.register'))
        self.assertTrue(re.search('Email', response.data))
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john_example.com',
            'username': 'john',
            'password': 'cat_cat',
            'password2': 'cat_catt'
        })
        self.assertTrue(re.search('请输入合法的邮箱地址', response.data))
        self.assertTrue(re.search('两个密码必须相同', response.data))
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertTrue('一封包含身份确认链接的邮件已发往你的邮箱' in response.data)
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        })
        self.assertTrue(re.search('Email已被占用', response.data))
        self.assertTrue(re.search('用户名已被占用', response.data))

    def test_02_login(self):
        # login with the new account
        User(email='john@example.com',
             password='cat_cat',
             username='john')
        response = self.client.get(url_for('auth.login'))
        self.assertTrue(re.search('忘记密码？', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john_example.com',
            'password': 'cat_cat'
        })
        self.assertTrue(re.search('请输入合法的邮箱地址', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_catt'
        })
        self.assertTrue(re.search('无效的用户名或密码', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.org',
            'password': 'cat_cat'
        })
        self.assertTrue(re.search('无效的用户名或密码', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue(re.search('你好', response.data))
        self.assertTrue('你还没有进行身份认证' in response.data)

    def test_03_confirm(self):
        # send a confirmation token
        user = User(email='john@example.com',
                    password='cat_cat',
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        token = 'asdhfjasdkhfadsfasdfasdf'
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue('确认链接非法或已过期' in response.data)
        response = self.client.get(url_for('auth.resend_confirmation'),
                                   follow_redirects=True)
        self.assertTrue('一封新的包含身份确认链接的邮件已发往你的邮箱' in response.data)
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        self.assertTrue('已确认你的身份，欢迎加入我们' in response.data)
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        self.assertTrue('Github' in response.data)
        response = self.client.get(url_for('auth.unconfirmed'), follow_redirects=True)
        self.assertTrue('Github' in response.data)

    def test_04_change_password(self):
        # change password
        User(email='john@example.com',
             password='cat_cat',
             confirmed=True,
             username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.password_change'))
        self.assertTrue('旧密码' in response.data)
        response = self.client.post(url_for('auth.password_change'), data={
            'old_password': 'cat_catt',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertTrue('请输入正确的密码' in response.data)
        response = self.client.post(url_for('auth.password_change'), data={
            'old_password': 'cat_cat',
            'password': 'cat_cat',
            'password2': 'cat_catt'
        }, follow_redirects=True)
        self.assertTrue('两个密码必须相同' in response.data)
        response = self.client.post(url_for('auth.password_change'), data={
            'old_password': 'cat_cat',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertTrue('修改成功' in response.data)

    def test_05_change_email(self):
        # change email
        user = User(email='john@example.com',
                    password='cat_cat',
                    confirmed=True,
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.send_confirmation_email'),
                                   follow_redirects=True)
        self.assertTrue('确认邮件已发送，请确认' in response.data)
        token = 'asdhfjasdkhfadsfasdfasdf'
        response = self.client.get(url_for('auth.email_change_confirm', token=token), follow_redirects=True)
        self.assertTrue('确认链接非法或已过期' in response.data)
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.email_change_confirm', token=token))
        self.assertTrue('修改邮箱地址' in response.data)
        response = self.client.post(url_for('auth.email_change_confirm', token=token), data={
            'email': 'john_example.com'
        }, follow_redirects=True)
        self.assertTrue('请输入合法的邮箱地址' in response.data)
        response = self.client.post(url_for('auth.email_change_confirm', token=token), data={
            'email': 'john@example.com'
        }, follow_redirects=True)
        self.assertTrue('Email已被占用' in response.data)
        response = self.client.post(url_for('auth.email_change_confirm', token=token), data={
            'email': 'jack@example.com'
        }, follow_redirects=True)
        self.assertTrue('修改成功' in response.data)
        self.assertTrue('一封包含身份确认链接的邮件已发往你的新邮箱' in response.data)
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue('已确认你的身份，欢迎加入我们' in response.data)
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        self.assertTrue('Github' in response.data)

    def test_06_logout(self):
        # log out
        User(email='john@example.com',
             password='cat_cat',
             confirmed=True,
             username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)

    def test_07_reset_password(self):
        # reset password
        user = User(email='john@example.com',
                    password='cat_cat',
                    confirmed=True,
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.password_reset_request'))
        self.assertTrue(response.status_code == 404)
        token = 'asdhfjasdkhfadsfasdfasdf'
        response = self.client.get(url_for('auth.password_reset', token=token))
        self.assertTrue(response.status_code == 404)
        self.client.get(url_for('auth.logout'), follow_redirects=True)
        response = self.client.get(url_for('auth.password_reset_request'))
        self.assertTrue(response.status_code == 200)
        self.assertTrue('重设密码' in response.data)
        response = self.client.post(url_for('auth.password_reset_request'), data={
            'email': 'jack_example.com'
        })
        self.assertTrue('请输入合法的邮箱地址' in response.data)
        response = self.client.post(url_for('auth.password_reset_request'), data={
            'email': 'jack@example.com'
        }, follow_redirects=True)
        self.assertTrue('无效的账号' in response.data)
        response = self.client.post(url_for('auth.password_reset_request'), data={
            'email': 'john@example.com'
        }, follow_redirects=True)
        self.assertTrue('一封含有重设密码的链接已发给你，请注意查收' in response.data)
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertTrue('重设失败' in response.data)
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'john_example.com',
            'password': 'cat_cat',
            'password2': 'cat_catt'
        })
        self.assertTrue('密码重设' in response.data)
        self.assertTrue('请输入合法的邮箱地址' in response.data)
        self.assertTrue('两个密码必须一样' in response.data)
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'jack@example.com',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        })
        self.assertTrue('无效的账号' in response.data)
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertTrue('你的密码已重设' in response.data)

    def test_08_error_handler(self):
        response = self.client.get(url_for('main.forbidden'))
        self.assertTrue(response.status_code == 403)
        self.assertTrue(b'<h1 align="center">Forbidden</h1>' in response.data)
        response = self.client.get(url_for('main.page_not_found'))
        self.assertTrue(response.status_code == 404)
        self.assertTrue(b'<h1 align="center">NOT FOUND</h1>' in response.data)
        response = self.client.get(url_for('main.internal_server_error'))
        self.assertTrue(response.status_code == 500)
        self.assertTrue(b'<h1 align="center">Internal Server Error</h1>' in response.data)


class FlaskClientTestCase01(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        User.add_admin()
        User.add_test_user()
        Category.add_none()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_00_short_post(self):
        # login
        response = self.client.post(url_for('auth.login'), data={
            'email': 'Admin@CodeBlog.com',
            'password': '1234',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue('个人' in response.data)
        # new talk
        response = self.client.get(url_for('post.new_talk'))
        self.assertTrue('吐槽' in response.data)
        response = self.client.post(url_for('post.new_talk'), data={
            'body': 'test'
        }, follow_redirects=True)
        talk = Post.query.first()
        self.assertTrue('吐槽成功' in response.data)
        self.assertTrue('test' == talk.body)
        # worry entry
        response = self.client.get(url_for('post.edit_article', post_id=talk.id))
        self.assertTrue('NOT FOUND' in response.data)
        # edit talk
        response = self.client.post(url_for('post.edit_talk', post_id=talk.id), data={
            'body': 'test_changed'
        }, follow_redirects=True)
        self.assertTrue('test_changed' == talk.body)
        self.assertTrue('已修改' in response.data)
        # delete talk
        response = self.client.get(url_for('post.delete_post', post_id=talk.id), follow_redirects=True)
        self.assertTrue(Post.query.count() == 0)
        self.assertTrue('已删除' in response.data)

    def test_01_post(self):
        # login
        response = self.client.post(url_for('auth.login'), data={
            'email': 'Admin@CodeBlog.com',
            'password': '1234',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue('个人' in response.data)
        # new post
        response = self.client.get(url_for('post.new_article'))
        self.assertTrue('博文' in response.data)
        response = self.client.post(url_for('post.new_article'), data={
            'title': 'title',
            'summary': 'summary',
            'editor-markdown-doc': 'test',
            'category': 1,
            # worry tags
            'tags': 'TEST，test again'
        }, follow_redirects=True)
        self.assertTrue('请使用英文逗号‘,’来分隔标签' in response.data)
        response = self.client.post(url_for('post.new_article'), data={
            'title': 'title',
            'summary': 'summary',
            'editor-markdown-doc': 'test',
            'category': 1,
            'tags': 'TEST,test again'
        }, follow_redirects=True)
        post = Post.query.first()
        self.assertTrue('发文成功' in response.data)
        self.assertTrue('title' == post.title)
        self.assertTrue('summary' == post.summary)
        self.assertTrue('test' == post.body)
        self.assertTrue('None' == post.category.name)
        self.assertTrue('TEST' in [tag.content for tag in post.tags])
        self.assertTrue('test again' in [tag.content for tag in post.tags])
        # show post
        response = self.client.get(url_for('post.article', post_id=post.id))
        self.assertTrue('title' in response.data)
        # worry entry
        response = self.client.get(url_for('post.edit_talk', post_id=post.id))
        self.assertTrue('NOT FOUND' in response.data)
        # edit post
        new_category = Category(name='test', parent_category=Category.query.first())
        new_category.save()
        response = self.client.post(url_for('post.edit_article', post_id=post.id), data={
            'title': 'title again',
            'summary': 'summary again',
            'editor-markdown-doc': 'test again',
            'category': 2,
            'tags': 'TEST'
        }, follow_redirects=True)
        self.assertTrue('该文章已修改' in response.data)
        self.assertTrue('title again' == post.title)
        self.assertTrue('summary again' == post.summary)
        self.assertTrue('test again' == post.body)
        self.assertTrue('test' == post.category.name)
        self.assertFalse('test again' in [tag.content for tag in post.tags])
        self.assertTrue('TEST' in [tag.content for tag in post.tags])
        # worry user
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)
        response = self.client.post(url_for('auth.login'), data={
            'email': 'user@CodeBlog.com',
            'password': '1234',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue('个人' in response.data)
        response = self.client.get(url_for('post.edit_article', post_id=post.id))
        self.assertTrue('Forbidden' in response.data)
        response = self.client.get(url_for('post.delete_post', post_id=post.id), follow_redirects=True)
        self.assertTrue('Forbidden' in response.data)
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)
        response = self.client.post(url_for('auth.login'), data={
            'email': 'Admin@CodeBlog.com',
            'password': '1234',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue('个人' in response.data)
        # delete post
        response = self.client.get(url_for('post.delete_post', post_id=post.id), follow_redirects=True)
        self.assertTrue(Post.query.count() == 0)
        self.assertTrue('已删除' in response.data)
