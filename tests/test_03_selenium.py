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

            cls.client.get('http://localhost:5000/shutdown')
            cls.client.close()

            db.drop_all()
            db.session.remove()

            cls.app_context.pop()

    def setUp(self):
        self.base_rul = 'http://127.0.0.1:5000'
        if not self.client:
            self.skipTest('Web browser not available')

    def tearDown(self):
        pass

    def test_00_home_page(self):

        self.client.get(self.base_rul + '/')
        self.assertTrue(re.search('CodeBlog', self.client.page_source))

        self.client.find_element_by_link_text('登陆').click()
        self.assertTrue('<h4>登陆</h4>' in self.client.page_source)

        self.client.find_element_by_name('email').\
            send_keys('Admin@CodeBlog.com')
        self.client.find_element_by_name('password').send_keys('1234')
        self.client.find_element_by_name('submit').click()

        self.assertTrue(re.search('Demo', self.client.page_source))
        self.assertTrue('个人' in self.client.page_source)

if __name__ == '__main__':
    unittest.main()
