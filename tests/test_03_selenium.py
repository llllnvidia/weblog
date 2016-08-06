# -*- coding: utf-8 -*-
import unittest
import threading
import re
from app import create_app, db
from app.models.account import User, Role
from app.models.post import Category
from selenium import webdriver
import sys

reload(sys)
sys.setdefaultencoding('utf-8')


class SeleniumTestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        cls.base_url = 'http://127.0.0.1:5000'
        try:
            cls.client = webdriver.Firefox()
        except:
            pass

        if cls.client:
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            import logging
            logger = logging.getLogger('werkzeug')
            logger.setLevel("ERROR")

            db.create_all()
            Role.insert_roles()
            User.add_admin()
            User.add_test_user()
            Category.add_none()

            threading.Thread(target=cls.app.run).start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:

            cls.client.get(cls.base_url + '/shutdown')
            cls.client.close()

            db.drop_all()
            db.session.remove()

            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_register_and_login(self):

        self.client.get(self.base_url + '/auth/register')
        self.assertTrue('注册' in self.client.page_source)

        self.client.find_element_by_name('email').send_keys('susan@example.com')
        self.client.find_element_by_name('username').send_keys('susan')
        self.client.find_element_by_name('password').send_keys('123456')
        self.client.find_element_by_name('password2').send_keys('123456')
        self.client.find_element_by_name('submit').click()

        self.assertTrue('一封包含身份确认链接的邮件已发往你的邮箱' in self.client.page_source)
        self.client.find_element_by_link_text('登陆').click()
        self.client.find_element_by_name('email').send_keys('susan@example.com')
        self.client.find_element_by_name('password').send_keys('123456')
        self.client.find_element_by_name('submit').click()
        self.assertIn('你好, susan', self.client.page_source)

        user_susan = User.query.filter_by(username='susan').first()
        token = user_susan.generate_confirmation_token('email_confirm')
        self.client.get(self.base_url + '/auth/confirm/' + token)
        self.assertIn('已确认你的身份，欢迎加入我们', self.client.page_source)
        self.assertIn('栏目', self.client.page_source)
        self.assertIn('个人', self.client.page_source)


if __name__ == '__main__':
    unittest.main()
