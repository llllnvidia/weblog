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
        response = self.client.get('/')
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
        self.assertTrue(b'Forbidden' in response.data)
        response = self.client.get(url_for('main.page_not_found'))
        self.assertTrue(response.status_code == 404)
        self.assertTrue(b'NOT FOUND' in response.data)
        response = self.client.get(url_for('main.internal_server_error'))
        self.assertTrue(response.status_code == 500)
        self.assertTrue(b'Internal Server Error' in response.data)

    def test_09_shutdown(self):
        self.app.testing = False
        response = self.client.get('/shutdown')
        self.assertIn('NOT FOUND', response.data)
        self.app.testing = True
        response = self.client.get('/shutdown')
        self.assertIn('Internal Server Error', response.data)


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
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login_admin(self):
        response = self.client.post(url_for('auth.login'), data={
            'email': 'Admin@CodeBlog.com',
            'password': '1234',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue('个人' in response.data)

    def login_user(self):
        response = self.client.post(url_for('auth.login'), data={
            'email': 'user@CodeBlog.com',
            'password': '1234',
            'remember_me': True
        }, follow_redirects=True)
        self.assertTrue('个人' in response.data)

    def logout(self):
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)

    def new_talk(self):
        response = self.client.get(url_for('post.new_talk'))
        self.assertTrue('吐槽' in response.data)
        response = self.client.post(url_for('post.new_talk'), data={
            'body': 'test'
        }, follow_redirects=True)
        self.assertTrue('吐槽成功' in response.data)

    def new_post(self):
        response = self.client.post(url_for('post.new_article'), data={
            'title': 'title',
            'summary': 'summary',
            'editor-markdown-doc': 'test',
            'category': 1,
            'tags': 'TEST,test again'
        }, follow_redirects=True)
        self.assertTrue('发文成功' in response.data)

    def test_00_short_post(self):
        # login
        self.login_admin()
        # new talk
        self.new_talk()
        talk = Post.query.first()
        self.assertTrue('test' == talk.body)
        # worry entry
        response = self.client.get(url_for('post.article', post_id=talk.id))
        self.assertTrue('NOT FOUND' in response.data)
        response = self.client.get(url_for('post.edit_article', post_id=talk.id))
        self.assertTrue('NOT FOUND' in response.data)
        # edit talk
        response = self.client.get(url_for('post.edit_talk', post_id=talk.id))
        self.assertTrue('test' in response.data)
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
        self.login_admin()
        # new post with worry tags
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
        # new post
        self.new_post()
        post = Post.query.first()
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
        response = self.client.get(url_for('post.edit_article', post_id=post.id))
        self.assertTrue('title' in response.data)
        self.assertTrue('summary' in response.data)
        self.assertTrue('test' in response.data)
        self.assertTrue('test again' in response.data)
        self.assertTrue('None' in response.data)
        response = self.client.post(url_for('post.edit_article', post_id=post.id), data={
            'title': 'title again',
            'summary': 'summary again',
            'editor-markdown-doc': 'test again',
            'category': 2,
            'tags': 'TEST,TEST_TEST'
        }, follow_redirects=True)
        self.assertTrue('该文章已修改' in response.data)
        self.assertTrue('title again' == post.title)
        self.assertTrue('summary again' == post.summary)
        self.assertTrue('test again' == post.body)
        self.assertTrue('test' == post.category.name)
        self.assertFalse('test again' in [tag.content for tag in post.tags])
        self.assertTrue('TEST' in [tag.content for tag in post.tags])
        self.assertTrue('TEST_TEST' in [tag.content for tag in post.tags])
        response = self.client.post(url_for('post.edit_article', post_id=post.id), data={
            'title': 'title again',
            'summary': 'summary again',
            'editor-markdown-doc': 'test again',
            'category': 2,
            'tags': 'TEST,test again'
        }, follow_redirects=True)
        self.assertTrue('该文章已修改' in response.data)
        self.assertFalse('TEST_TEST' in [tag.content for tag in post.tags])
        self.assertTrue('TEST' in [tag.content for tag in post.tags])
        self.assertTrue('test again' in [tag.content for tag in post.tags])
        response = self.client.post(url_for('post.edit_article', post_id=post.id), data={
            'title': 'title again',
            'summary': 'summary again',
            'editor-markdown-doc': 'test again',
            'category': 2,
            'tags': ''
        }, follow_redirects=True)
        self.assertTrue('该文章已修改' in response.data)
        self.assertTrue(len(post.tags) == 0)
        # worry user
        self.logout()
        self.login_user()
        response = self.client.get(url_for('post.edit_article', post_id=post.id))
        self.assertTrue('Forbidden' in response.data)
        response = self.client.get(url_for('post.delete_post', post_id=post.id), follow_redirects=True)
        self.assertTrue('Forbidden' in response.data)
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)
        self.login_admin()
        # delete post
        response = self.client.get(url_for('post.delete_post', post_id=post.id), follow_redirects=True)
        self.assertTrue(Post.query.count() == 0)
        self.assertTrue('已删除' in response.data)

    def test_02_comment(self):
        # login
        self.login_admin()
        # new post
        self.new_post()
        post = Post.query.first()
        # new comment
        response = self.client.post(url_for('post.article', post_id=post.id), data={
            'body': 'test comment'
        }, follow_redirects=True)
        self.assertTrue('你的评论已提交' in response.data)
        # user is none
        self.logout()
        response = self.client.post(url_for('post.article', post_id=post.id), data={
            'body': 'test comment'
        }, follow_redirects=True)
        self.assertIn('请先登录', response.data)

    def test_03_neighbourhood(self):
        response = self.client.get(url_for('main.neighbourhood'))
        self.assertIn('无栏目', response.data)
        self.assertIn('无标签', response.data)
        self.assertIn('无文章', response.data)
        category_other = Category(name='other', parent_category=Category.query.first())
        category_other.save()
        category_test = Category(name='test', parent_category=Category.query.first())
        category_test.save()
        tag_one = Tag(content='tag_one')
        tag_one.save()
        tag_two = Tag(content='tag_two')
        tag_two.save()
        talk_test = Post(body='test_talk', author=User.query.get(2))
        talk_test.save()
        article_test = Post(title='article_title', summary='article_summary', body='#article_body',
                            category=category_test, author=User.query.first(), is_article=True)
        article_test.save()
        article_test.tag(tag_one)
        article_test.tag(tag_two)
        response = self.client.get(url_for('main.neighbourhood'))
        self.assertNotIn('无栏目', response.data)
        self.assertNotIn('无标签', response.data)
        self.assertNotIn('无文章', response.data)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('吐槽', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        self.assertNotIn('article_body', response.data)
        # get key
        response = self.client.get('/neighbourhood?key=article', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        response = self.client.get('/neighbourhood?key=talk', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('tag_one', response.data)
        response = self.client.get('/neighbourhood?key_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get category
        response = self.client.get('/neighbourhood?category=other', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('无标签', response.data)
        self.assertIn('无文章', response.data)
        response = self.client.get('/neighbourhood?category=test', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        response = self.client.get('/neighbourhood?category_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # show talk
        response = self.client.get('/neighbourhood?show_talk=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('无标签', response.data)
        response = self.client.get('/neighbourhood?category=test', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        response = self.client.get('/neighbourhood?category_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # show followed
        self.login_admin()
        response = self.client.get('/neighbourhood?show_followed=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.logout()
        # get tag
        self.client.get('/neighbourhood')
        response = self.client.get('/neighbourhood?tag=tag_one', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/neighbourhood?tag=tag_two', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        self.client.get('/neighbourhood?tag=tag_one', follow_redirects=True)
        response = self.client.get('/neighbourhood?tag=tag_two', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/neighbourhood?tag_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)

    def test_04_user_page(self):
        response = self.client.get(url_for('main.user', username='Nobody'))
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get(url_for('main.user', username='Admin'))
        self.assertIn('Admin', response.data)
        self.assertIn('无栏目', response.data)
        self.assertIn('无标签', response.data)
        self.assertIn('无文章', response.data)
        response = self.client.get(url_for('main.user', username='tester'))
        self.assertIn('tester', response.data)
        self.assertIn('无栏目', response.data)
        self.assertIn('无标签', response.data)
        self.assertIn('无文章', response.data)
        category_other = Category(name='other', parent_category=Category.query.first())
        category_other.save()
        category_test = Category(name='test', parent_category=Category.query.first())
        category_test.save()
        tag_one = Tag(content='tag_one')
        tag_one.save()
        tag_two = Tag(content='tag_two')
        tag_two.save()
        talk_test = Post(body='test_talk', author=User.query.first())
        talk_test.save()
        article_test_one = Post(title='article_title', summary='article_summary', body='#article_body',
                                category=category_test, author=User.query.first(), is_article=True)
        article_test_one.save()
        article_test_two = Post(title='article', summary='article', body='#article',
                                category=category_other, author=User.query.first(), is_article=True)
        article_test_two.save()
        article_test_one.tag(tag_one)
        article_test_one.tag(tag_two)
        response = self.client.get('/user/Admin')
        self.assertNotIn('无栏目', response.data)
        self.assertNotIn('无标签', response.data)
        self.assertNotIn('无文章', response.data)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('吐槽', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        self.assertNotIn('article_body', response.data)
        # get key
        response = self.client.get('/user/Admin?key=article', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        response = self.client.get('/user/Admin?key=talk', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('tag_one', response.data)
        response = self.client.get('/user/Admin?key_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get category
        response = self.client.get('/user/Admin?category=other', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertNotIn('article_title', response.data)
        self.assertIn('article', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('无标签', response.data)
        response = self.client.get('/user/Admin?category=test', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        response = self.client.get('/user/Admin?category_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # show talk
        response = self.client.get('/user/Admin?show_talk=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('无标签', response.data)
        response = self.client.get('/user/Admin?category=test', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        response = self.client.get('/user/Admin?category_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get tag
        response = self.client.get('/user/Admin?tag=tag_one', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/user/Admin?tag=tag_two', follow_redirects=True)
        self.assertNotIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        self.client.get('/user/Admin?tag=tag_one', follow_redirects=True)
        response = self.client.get('/user/Admin?tag=tag_two', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/user/Admin?tag_disable=1', follow_redirects=True)
        self.assertIn('test_talk', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)

    def test_05_follow(self):
        self.login_admin()
        response = self.client.get(url_for('main.follow', username='test'), follow_redirects=True)
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get(url_for('main.follow', username='tester'), follow_redirects=True)
        self.assertIn('tester', response.data)
        self.assertIn('取消关注', response.data)
        response = self.client.get(url_for('main.follow', username='tester'), follow_redirects=True)
        self.assertIn('你已经关注了tester', response.data)
        response = self.client.get(url_for('main.followed_by', username='Admin'))
        self.assertIn('tester', response.data)
        response = self.client.get(url_for('main.followers', username='tester'))
        self.assertIn('Admin', response.data)
        response = self.client.get(url_for('main.followed_by', username='test'))
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get(url_for('main.followers', username='test'))
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get(url_for('main.not_follow', username='test'), follow_redirects=True)
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get(url_for('main.not_follow', username='tester'), follow_redirects=True)
        self.assertIn('tester', response.data)
        self.assertIn('关注', response.data)
        response = self.client.get(url_for('main.not_follow', username='tester'), follow_redirects=True)
        self.assertIn('你没有关注过tester', response.data)

    def test_06_edit_profile(self):
        self.login_user()
        response = self.client.get(url_for('main.edit_profile'))
        self.assertIn('修改资料', response.data)
        response = self.client.post(url_for('main.edit_profile'), data={
            'name': 'Susan',
            'location': 'city',
            'about': ''
        }, follow_redirects=True)
        self.assertIn('你的资料已修改', response.data)
        self.assertIn('Susan', response.data)
        self.assertIn('city', response.data)

    def test_07_message(self):
        self.login_user()
        response = self.client.get(url_for('main.dialogues'))
        self.assertIn('系统消息', response.data)
        response = self.client.post(url_for('main.dialogues', dialogue_id=1), data={
            'content': 'test chat'
        }, follow_redirects=True)
        self.assertIn('test chat', response.data)
        self.assertNotIn('没有聊天记录', response.data)
        self.logout()
        self.login_admin()
        response = self.client.get('/')
        self.assertIn('个人 <span class="badge badge-xs">1</span>', response.data)
        response = self.client.get(url_for('main.dialogues'))
        self.assertIn('tester', response.data)
        response = self.client.get(url_for('main.dialogues', dialogue_id=1))
        self.assertNotIn('个人 <span class="badge badge-xs">1</span>', response.data)
        self.assertIn('test chat', response.data)
        response = self.client.get('/dialogues/1?delete_true=1', follow_redirects=True)
        self.assertNotIn('tester', response.data)
        response = self.client.get(url_for('main.dialogues', dialogue_id=1))
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get(url_for('main.new_dialogue', username='tester'), follow_redirects=True)
        self.assertIn('tester', response.data)
        self.logout()
        user_tester2 = User(username='tester2')
        user_tester2.save()
        self.login_user()
        response = self.client.get(url_for('main.new_dialogue', username='tester2'), follow_redirects=True)
        self.assertIn('tester2', response.data)

    def test_08_users(self):
        # worry user
        self.login_user()
        response = self.client.get(url_for('admin_manager.users'))
        self.assertIn('Forbidden', response.data)
        self.logout()
        # right user
        self.login_admin()
        response = self.client.get(url_for('admin_manager.users'))
        self.assertIn('tester', response.data)
        self.assertIn('Admin', response.data)
        # edit profile
        response = self.client.get(url_for('admin_manager.edit_profile_admin', user_id=2))
        self.assertIn('user@CodeBlog.com', response.data)
        response = self.client.post(url_for('admin_manager.edit_profile_admin', user_id=2), data={
            'email': 'tester@CodeBlog.com',
            'username': 'tester?',
            'confirmed': True,
            'role': 1,
            'name': '',
            'location': '',
            'about_me': ''
        }, follow_redirects=True)
        self.assertIn('资料已修改', response.data)
        self.assertNotIn('user@CodeBlog.com', response.data)
        self.assertIn('tester?', response.data)
        # delete user
        response = self.client.get(url_for('admin_manager.delete_user', user_id=2), follow_redirects=True)
        self.assertIn('已删除', response.data)
        self.assertNotIn('tester?', response.data)
        # new user
        response = self.client.post(url_for('admin_manager.edit_profile_admin'), data={
            'email': 'tester@CodeBlog.com',
            'username': 'tester?',
            'confirmed': True,
            'role': 1,
            'name': '',
            'location': '',
            'about_me': ''
        }, follow_redirects=True)
        self.assertIn('用户创建成功', response.data)
        self.assertIn('tester?', response.data)

    def test_09_moderate(self):
        self.login_admin()
        response = self.client.get(url_for('admin_manager.moderate'))
        self.assertIn('所有评论', response.data)
        self.new_post()
        post = Post.query.first()
        post.save()
        comment = Comment(body='test comment', post=post)
        comment.save()
        response = self.client.get(url_for('admin_manager.moderate'))
        self.assertIn('test comment', response.data)
        response = self.client.get(url_for('admin_manager.moderate_disable', comment_id=1), follow_redirects=True)
        self.assertIn('禁止显示', response.data)
        response = self.client.get(url_for('admin_manager.moderate_enable', comment_id=1), follow_redirects=True)
        self.assertIn('解禁成功', response.data)

    def test_10_categories(self):
        self.login_admin()
        response = self.client.get(url_for('admin_manager.categories'))
        self.assertIn('所有栏目', response.data)
        self.assertIn('None', response.data)
        category = Category(name='other', parent_category=Category.query.first())
        category.save()
        response = self.client.get(url_for('admin_manager.categories'))
        self.assertIn('other', response.data)
        response = self.client.post(url_for('admin_manager.categories', category_id=2), data={
            'name': '其他',
            'parent': 1
        }, follow_redirects=True)
        self.assertIn('其他', response.data)
        response = self.client.get(url_for('admin_manager.delete_category', category_id=2), follow_redirects=True)
        self.assertNotIn('其他', response.data)

    def test_11_talks(self):
        self.login_user()
        self.new_talk()
        self.logout()
        self.login_admin()
        self.new_talk()
        response = self.client.get(url_for('admin_manager.talks'))
        self.assertIn('所有吐槽', response.data)
        self.assertIn('test', response.data)
        talk_one = Post.query.first()
        response = self.client.get('/delete/post/%s?next=/admin_manager/talks' % talk_one.id, follow_redirects=True)
        self.assertIn('所有吐槽', response.data)
        self.assertIn('test', response.data)
        talk_two = Post.query.first()
        response = self.client.get('/delete/post/%s?next=/admin_manager/talks' % talk_two.id, follow_redirects=True)
        self.assertIn('所有吐槽', response.data)
        self.assertNotIn('test', response.data)

    def test_12_articles(self):
        self.login_admin()
        self.new_post()
        response = self.client.get(url_for('admin_manager.articles'))
        self.assertIn('所有博文', response.data)
        self.assertIn('summary', response.data)
        post = Post.query.first()
        response = self.client.get('/delete/post/%s?next=/admin_manager/articles' % post.id, follow_redirects=True)
        self.assertIn('所有博文', response.data)
        self.assertNotIn('summary', response.data)

    def test_13_tags(self):
        self.login_admin()
        self.new_post()
        response = self.client.get(url_for('admin_manager.tags'))
        self.assertIn('所有标签', response.data)
        self.assertIn('TEST', response.data)
        self.assertIn('test again', response.data)
        self.client.get(url_for('admin_manager.delete_tag', tag_id=1))
        response = self.client.get(url_for('admin_manager.delete_tag', tag_id=2), follow_redirects=True)
        self.assertIn('所有标签', response.data)
        self.assertNotIn('TEST', response.data)
        self.assertNotIn('test again', response.data)


if __name__ == '__main__':
    unittest.main()


