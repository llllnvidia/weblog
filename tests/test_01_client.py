# -*- coding: utf-8 -*-
import re
import unittest
from flask import url_for
from app import create_app, db
from app.models.account import User, Role


class FlaskClientTestCase(unittest.TestCase):
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
            'password': 'cat',
            'password2': 'ca'
        })
        self.assertTrue(re.search('请输入合法的邮箱地址。', response.data))
        self.assertTrue(re.search('两个密码必须相同。', response.data))
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertTrue(response.status_code == 302)
        response = self.client.get(url_for('auth.register'))
        self.assertTrue('一封包含身份确认链接的邮件已发往你的邮箱。' in response.data)
        response = self.client.post(url_for('auth.register'), data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertTrue(re.search('Email已被占用。', response.data))
        self.assertTrue(re.search('用户名已被占用。', response.data))

    def test_02_login(self):
        # login with the new account
        User(email='john@example.com',
             password='cat',
             username='john')
        response = self.client.get(url_for('auth.login'))
        self.assertTrue(re.search('忘记密码？', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john_example.com',
            'password': 'cat'
        })
        self.assertTrue(re.search('请输入合法的邮箱地址。', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'ca'
        })
        self.assertTrue(re.search('无效的用户名或密码', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.org',
            'password': 'cat'
        })
        self.assertTrue(re.search('无效的用户名或密码', response.data))
        response = self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue(re.search('你好', response.data))
        self.assertTrue('你还没有进行身份认证。' in response.data)

    def test_03_confirm(self):
        # send a confirmation token
        user = User(email='john@example.com',
                    password='cat',
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
            'remember_me': True
        }, follow_redirects=True)
        token = 'asdhfjasdkhfadsfasdfasdf'
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue('确认链接非法或已过期。' in response.data)
        response = self.client.get(url_for('auth.resend_confirmation'),
                                   follow_redirects=True)
        self.assertTrue('一封新的包含身份确认链接的邮件已发往你的邮箱。' in response.data)
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        self.assertTrue('已确认你的身份，欢迎加入我们。' in response.data)
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        self.assertTrue('Github' in response.data)
        response = self.client.get(url_for('auth.unconfirmed'), follow_redirects=True)
        self.assertTrue('Github' in response.data)

    def test_04_change_password(self):
        # change password
        User(email='john@example.com',
             password='cat',
             confirmed=True,
             username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.password_change'))
        self.assertTrue('旧密码' in response.data)
        response = self.client.post(url_for('auth.password_change'), data={
            'old_password': 'ca',
            'password': 'cat',
            'password2': 'cat'
        }, follow_redirects=True)
        self.assertTrue('请输入正确的密码。' in response.data)
        response = self.client.post(url_for('auth.password_change'), data={
            'old_password': 'cat',
            'password': 'cat',
            'password2': 'ca'
        }, follow_redirects=True)
        self.assertTrue('两个密码必须相同。' in response.data)
        response = self.client.post(url_for('auth.password_change'), data={
            'old_password': 'cat',
            'password': 'cat',
            'password2': 'cat'
        }, follow_redirects=True)
        self.assertTrue('修改成功。' in response.data)

    def test_05_change_email(self):
        # change email
        user = User(email='john@example.com',
                    password='cat',
                    confirmed=True,
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.send_confirmation_email'),
                                   follow_redirects=True)
        self.assertTrue('确认邮件已发送，请确认。' in response.data)
        token = 'asdhfjasdkhfadsfasdfasdf'
        response = self.client.get(url_for('auth.email_change_confirm', token=token), follow_redirects=True)
        self.assertTrue('确认链接非法或已过期。' in response.data)
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.email_change_confirm', token=token))
        self.assertTrue('修改邮箱地址' in response.data)
        response = self.client.post(url_for('auth.email_change_confirm', token=token), data={
            'email': 'john_example.com'
        }, follow_redirects=True)
        self.assertTrue('请输入合法的邮箱地址。' in response.data)
        response = self.client.post(url_for('auth.email_change_confirm', token=token), data={
            'email': 'john@example.com'
        }, follow_redirects=True)
        self.assertTrue('Email已被占用' in response.data)
        response = self.client.post(url_for('auth.email_change_confirm', token=token), data={
            'email': 'jack@example.com'
        }, follow_redirects=True)
        self.assertTrue('修改成功。' in response.data)
        self.assertTrue('一封包含身份确认链接的邮件已发往你的新邮箱。' in response.data)
        token = user.generate_confirmation_token()
        response = self.client.get(url_for('auth.confirm', token=token),
                                   follow_redirects=True)
        self.assertTrue('已确认你的身份，欢迎加入我们。' in response.data)
        response = self.client.get(url_for('auth.confirm', token=token), follow_redirects=True)
        self.assertTrue('Github' in response.data)

    def test_06_logout(self):
        # log out
        User(email='john@example.com',
             password='cat',
             confirmed=True,
             username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
            'remember_me': True
        }, follow_redirects=True)
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)

    def test_07_reset_password(self):
        # reset password
        user = User(email='john@example.com',
                    password='cat',
                    confirmed=True,
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat',
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
        self.assertTrue('请输入合法的邮箱地址。' in response.data)
        response = self.client.post(url_for('auth.password_reset_request'), data={
            'email': 'jack@example.com'
        }, follow_redirects=True)
        self.assertTrue('无效的账号。' in response.data)
        response = self.client.post(url_for('auth.password_reset_request'), data={
            'email': 'john@example.com'
        }, follow_redirects=True)
        self.assertTrue('一封含有重设密码的链接已发给你，请注意查收。' in response.data)
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'john@example.com',
            'password': 'cat',
            'password2': 'cat'
        }, follow_redirects=True)
        self.assertTrue('重设失败。' in response.data)
        token = user.generate_reset_token()
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'john_example.com',
            'password': 'cat',
            'password2': 'ca'
        })
        self.assertTrue('密码重设' in response.data)
        self.assertTrue('请输入合法的邮箱地址。' in response.data)
        self.assertTrue('两个密码必须一样。' in response.data)
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'jack@example.com',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertTrue('无效的账号。' in response.data)
        response = self.client.post(url_for('auth.password_reset', token=token), data={
            'email': 'john@example.com',
            'password': 'cat',
            'password2': 'cat'
        }, follow_redirects=True)
        self.assertTrue('你的密码已重设。' in response.data)

    def test_08_error_handler(self):
        response = self.client.get(url_for('auth.forbidden'))
        self.assertTrue(response.status_code == 403)
        self.assertTrue(b'<h1 align="center">Forbidden</h1>' in response.data)
        response = self.client.get(url_for('auth.page_not_found'))
        self.assertTrue(response.status_code == 404)
        self.assertTrue(b'<h1 align="center">NOT FOUND</h1>' in response.data)
        response = self.client.get(url_for('auth.internal_server_error'))
        self.assertTrue(response.status_code == 500)
        self.assertTrue(b'<h1 align="center">Internal Server Error</h1>' in response.data)
