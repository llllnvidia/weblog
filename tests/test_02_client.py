# -*- coding: utf-8 -*-
import re
import unittest
from time import sleep
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

    def test_register(self):
        # register a new account
        response = self.client.get('/auth/register')
        self.assertIn('Email', response.data)
        response = self.client.post('/auth/register', data={
            'email': 'john_example.com',
            'username': 'john',
            'password': 'cat_cat',
            'password2': 'cat_catt'
        })
        self.assertIn('请输入合法的邮箱地址', response.data)
        self.assertIn('两个密码必须相同', response.data)
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertIn('一封包含身份确认链接的邮件已发往你的邮箱', response.data)
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        })
        self.assertIn('Email已被占用', response.data)
        self.assertIn('用户名已被占用', response.data)

    def test_login(self):
        # login with the new account
        User(email='john@example.com',
             password='cat_cat',
             username='john')
        response = self.client.get('/auth/login')
        self.assertTrue(re.search('忘记密码？', response.data))
        response = self.client.post('/auth/login', data={
            'email': 'john_example.com',
            'password': 'cat_cat'
        })
        self.assertIn('请输入合法的邮箱地址', response.data)
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_catt'
        })
        self.assertIn('无效的用户名或密码', response.data)
        response = self.client.post('/auth/login', data={
            'email': 'john@example.org',
            'password': 'cat_cat'
        })
        self.assertIn('无效的用户名或密码', response.data)
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        }, follow_redirects=True)
        self.assertIn('你好', response.data)
        self.assertIn('你还没有进行身份认证', response.data)

    def test_confirm(self):
        # send a confirmation token
        user = User(email='john@example.com',
                    password='cat_cat',
                    username='john')
        self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        })
        token = r"\x87\xb7t\xcc\x84\x1e\xff"
        response = self.client.get('/auth/confirm/%s' % token,
                                   follow_redirects=True)
        self.assertIn('确认链接非法或已过期', response.data)
        response = self.client.get('/auth/confirm',
                                   follow_redirects=True)
        self.assertIn('一封新的包含身份确认链接的邮件已发往你的邮箱', response.data)
        token = user.generate_confirmation_token('email_confirm')
        response = self.client.get('/auth/confirm/%s' % token, follow_redirects=True)
        self.assertIn('已确认你的身份，欢迎加入我们', response.data)
        response = self.client.get('/auth/confirm/%s' % token, follow_redirects=True)
        self.assertIn('栏目', response.data)
        response = self.client.get('/auth/unconfirmed', follow_redirects=True)
        self.assertIn('栏目', response.data)

    def test_change_password(self):
        # change password
        User(email='john@example.com',
             password='cat_cat',
             confirmed=True,
             username='john')
        self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        })
        response = self.client.get('/auth/PasswordChange/')
        self.assertIn('旧密码', response.data)
        response = self.client.post('/auth/PasswordChange/', data={
            'old_password': 'cat_catt',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertIn('请输入正确的密码', response.data)
        response = self.client.post('/auth/PasswordChange/', data={
            'old_password': 'cat_cat',
            'password': 'cat_cat',
            'password2': 'cat_catt'
        }, follow_redirects=True)
        self.assertIn('两个密码必须相同', response.data)
        response = self.client.post('/auth/PasswordChange/', data={
            'old_password': 'cat_cat',
            'password': 'cat_catt',
            'password2': 'cat_catt'
        }, follow_redirects=True)
        self.assertIn('修改成功', response.data)
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_catt',
            'remember_me': True
        }, follow_redirects=True)
        self.assertIn('个人', response.data)

    def test_change_email(self):
        # change email
        user = User(email='john@example.com',
                    password='cat_cat',
                    confirmed=True,
                    username='john')
        self.client.post(url_for('auth.login'), data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        })
        response = self.client.get('/auth/reset/email',
                                   follow_redirects=True)
        self.assertIn('确认邮件已发送，请确认', response.data)
        token = r"\x87\xb7t\xcc\x84\x1e\xff"
        response = self.client.get('/auth/reset/email/%s' % token, follow_redirects=True)
        self.assertIn('确认链接非法或已过期', response.data)
        token = user.generate_confirmation_token('change_email_confirm')
        response = self.client.get('/auth/reset/email/%s' % token)
        self.assertIn('修改邮箱地址', response.data)
        response = self.client.post('/auth/reset/email/%s' % token, data={
            'email': 'john_example.com'
        }, follow_redirects=True)
        self.assertIn('请输入合法的邮箱地址', response.data)
        response = self.client.post('/auth/reset/email/%s' % token, data={
            'email': 'john@example.com'
        }, follow_redirects=True)
        self.assertIn('Email已被占用', response.data)
        response = self.client.post('/auth/reset/email/%s' % token, data={
            'email': 'jack@example.com'
        }, follow_redirects=True)
        self.assertIn('修改成功', response.data)
        self.assertIn('一封包含身份确认链接的邮件已发往你的新邮箱', response.data)
        token = user.generate_confirmation_token('email_confirm')
        response = self.client.get('/auth/confirm/%s' % token, follow_redirects=True)
        self.assertIn('已确认你的身份，欢迎加入我们', response.data)

    def test_logout(self):
        # log out
        User(email='john@example.com',
             password='cat_cat',
             confirmed=True,
             username='john')
        self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        })
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertIn('已注销', response.data)

    def test_reset_password(self):
        # reset password
        user = User(email='john@example.com',
                    password='cat_cat',
                    confirmed=True,
                    username='john')
        self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'remember_me': True
        })
        response = self.client.get('/auth/reset/password')
        self.assertEqual(response.status_code, 404)
        token = r"\x87\xb7t\xcc\x84\x1e\xff"
        response = self.client.get('/auth/reset/password/%s' % token)
        self.assertEqual(response.status_code, 404)
        self.client.get('/auth/logout')
        response = self.client.get('/auth/reset/password')
        self.assertEqual(response.status_code, 200)
        self.assertIn('重设密码', response.data)
        response = self.client.post('/auth/reset/password', data={
            'email': 'jack_example.com'
        })
        self.assertIn('请输入合法的邮箱地址', response.data)
        response = self.client.post('/auth/reset/password', data={
            'email': 'jack@example.com'
        }, follow_redirects=True)
        self.assertIn('无效的账号', response.data)
        response = self.client.post('/auth/reset/password', data={
            'email': 'john@example.com'
        }, follow_redirects=True)
        self.assertIn('一封含有重设密码的链接已发给你，请注意查收', response.data)
        response = self.client.post('/auth/reset/password/%s' % token, data={
            'email': 'john@example.com',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        }, follow_redirects=True)
        self.assertIn('重设失败', response.data)
        token = user.generate_confirmation_token('reset_password')
        response = self.client.post('/auth/reset/password/%s' % token, data={
            'email': 'john_example.com',
            'password': 'cat_cat',
            'password2': 'cat_catt'
        })
        self.assertIn('密码重设', response.data)
        self.assertIn('请输入合法的邮箱地址', response.data)
        self.assertIn('两个密码必须一样', response.data)
        response = self.client.post('/auth/reset/password/%s' % token, data={
            'email': 'jack@example.com',
            'password': 'cat_cat',
            'password2': 'cat_cat'
        })
        self.assertIn('无效的账号', response.data)
        response = self.client.post('/auth/reset/password/%s' % token, data={
            'email': 'john@example.com',
            'password': 'cat_catt',
            'password2': 'cat_catt'
        }, follow_redirects=True)
        self.assertIn('你的密码已重设', response.data)
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat_catt',
            'remember_me': True
        }, follow_redirects=True)
        self.assertIn('个人', response.data)

    def test_error_handler(self):
        response = self.client.get('/forbidden')
        self.assertEqual(response.status_code, 403)
        self.assertIn('Forbidden', response.data)
        response = self.client.get('/page_not_found')
        self.assertEqual(response.status_code, 404)
        self.assertIn('NOT FOUND', response.data)
        response = self.client.get('/internal_server_error')
        self.assertEqual(response.status_code, 500)
        self.assertIn('Internal Server Error', response.data)

    def test_shutdown(self):
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

    def login(self, username, password):
        response = self.client.post(url_for('auth.login'), data={
            'email': '%s@CodeBlog.com' % username,
            'password': '%s' % password,
            'remember_me': True
        }, follow_redirects=True)
        self.assertIn('个人', response.data)

    def logout(self):
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertIn('已注销', response.data)

    def new_post(self):
        response = self.client.post(url_for('post.new_article'), data={
            'title': 'title',
            'summary': 'summary',
            'editor-markdown-doc': 'test',
            'category': 1,
            'tags': 'TEST,test again'
        }, follow_redirects=True)
        self.assertIn('发文成功', response.data)

    def test_post(self):
        # login
        self.login(username='Admin', password='1234')
        # new post with worry tags
        response = self.client.get(url_for('post.new_article'))
        self.assertIn('博文', response.data)
        response = self.client.post(url_for('post.new_article'), data={
            'title': 'title',
            'summary': 'summary',
            'editor-markdown-doc': 'test',
            'category': 1,
            # worry tags
            'tags': 'TEST，test again'
        }, follow_redirects=True)
        self.assertIn('请使用英文逗号‘,’来分隔标签', response.data)
        # new post
        self.new_post()
        post = Post.query.first()
        self.assertEqual('title', post.title)
        self.assertEqual('summary', post.summary)
        self.assertEqual('test', post.body)
        self.assertEqual('None', post.category.name)
        self.assertIn('TEST', [tag.content for tag in post.tags])
        self.assertIn('test again', [tag.content for tag in post.tags])
        # show post
        response = self.client.get(url_for('post.article', post_id=post.id))
        self.assertIn('title', response.data)
        # edit post
        new_category = Category(name='test', parent_category=Category.query.first())
        new_category.save()
        response = self.client.get(url_for('post.edit_article', post_id=post.id))
        self.assertIn('title', response.data)
        self.assertIn('summary', response.data)
        self.assertIn('test', response.data)
        self.assertIn('test again', response.data)
        self.assertIn('None', response.data)
        response = self.client.post(url_for('post.edit_article', post_id=post.id), data={
            'title': 'title again',
            'summary': 'summary again',
            'editor-markdown-doc': 'test again',
            'category': 2,
            'tags': 'TEST,TEST_TEST'
        }, follow_redirects=True)
        self.assertIn('该文章已修改', response.data)
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
        self.login(username='user', password='1234')
        response = self.client.get(url_for('post.edit_article', post_id=post.id))
        self.assertTrue('Forbidden' in response.data)
        response = self.client.get(url_for('post.delete_post', post_id=post.id), follow_redirects=True)
        self.assertTrue('Forbidden' in response.data)
        response = self.client.get(url_for('auth.logout'), follow_redirects=True)
        self.assertTrue('已注销' in response.data)
        self.login(username='Admin', password='1234')
        # delete post
        response = self.client.get(url_for('post.delete_post', post_id=post.id), follow_redirects=True)
        self.assertTrue(Post.query.count() == 0)
        self.assertIn('已删除', response.data)

    def test_post_is_draft(self):
        self.login(username='Admin', password='1234')
        response = self.client.post('/new/article', data={
            'title': 'title',
            'summary': 'summary',
            'editor-markdown-doc': 'test',
            'category': 1,
            'tags': 'TEST,test again',
            'is_draft': True
        }, follow_redirects=True)
        self.assertIn('发文成功', response.data)
        response = self.client.get('/')
        self.assertIn('无文章', response.data)
        response = self.client.get('/user/Admin')
        self.assertNotIn('无文章', response.data)
        self.assertIn('test again', response.data)
        self.logout()
        self.login(username='user', password='1234')
        response = self.client.get('/article/1', follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        response = self.client.get('/')
        self.assertIn('无文章', response.data)
        response = self.client.get('/user/Admin')
        self.assertIn('无文章', response.data)
        self.assertNotIn('test again', response.data)

    def test_comment(self):
        # login
        self.login(username='Admin', password='1234')
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

    def test_neighbourhood(self):
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
        article_test = Post(title='article_title', summary='article_summary', body='#article_body',
                            category=category_test, author=User.query.first())
        article_test.save()
        article_test.tag(tag_one)
        article_test.tag(tag_two)
        article_test.save()
        response = self.client.get(url_for('main.neighbourhood'))
        self.assertNotIn('无栏目', response.data)
        self.assertNotIn('无标签', response.data)
        self.assertNotIn('无文章', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        self.assertNotIn('article_body', response.data)
        # get key
        response = self.client.get('/?key=article', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        response = self.client.get('/?key=ABC', follow_redirects=True)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('article_summary', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        self.assertIn('无标签', response.data)
        self.assertIn('无文章', response.data)
        response = self.client.get('/?key_disable=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get category
        response = self.client.get('/?category=other', follow_redirects=True)
        self.assertNotIn('article_title', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('无标签', response.data)
        self.assertIn('无文章', response.data)
        response = self.client.get('/?category=test', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        response = self.client.get('/?category_disable=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # show followed
        self.login(username='Admin', password='1234')
        response = self.client.get('/?show_followed=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.logout()
        # get tag
        self.client.get('/')
        response = self.client.get('/?tag=tag_one', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/?tag=tag_two', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        self.client.get('/?tag=tag_one', follow_redirects=True)
        response = self.client.get('/?tag=tag_two', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/?tag_disable=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get something with prev_url
        response = self.client.get('/?tag=tag_one&prev_url=/article', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertNotIn('无标签', response.data)
        response = self.client.get('/?category=test&prev_url=/article', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)

    def test_user_page(self):
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
        article_test_one = Post(title='article_title', summary='article_summary', body='#article_body',
                                category=category_test, author=User.query.first())
        article_test_one.save()
        article_test_two = Post(title='article', summary='article', body='#article',
                                category=category_other, author=User.query.first())
        article_test_two.save()
        article_test_one.tag(tag_one)
        article_test_one.tag(tag_two)
        response = self.client.get('/user/Admin')
        self.assertNotIn('无栏目', response.data)
        self.assertNotIn('无标签', response.data)
        self.assertNotIn('无文章', response.data)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        self.assertNotIn('article_body', response.data)
        # get key
        response = self.client.get('/user/Admin?key=article', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('article_summary', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('other', response.data)
        self.assertIn('test', response.data)
        response = self.client.get('/user/Admin?key_disable=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get category
        response = self.client.get('/user/Admin?category=other', follow_redirects=True)
        self.assertNotIn('article_title', response.data)
        self.assertIn('article', response.data)
        self.assertNotIn('tag_one', response.data)
        self.assertIn('无标签', response.data)
        response = self.client.get('/user/Admin?category=test', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        response = self.client.get('/user/Admin?category_disable=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get tag
        response = self.client.get('/user/Admin?tag=tag_one', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/user/Admin?tag=tag_two', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        self.client.get('/user/Admin?tag=tag_one', follow_redirects=True)
        response = self.client.get('/user/Admin?tag=tag_two', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertIn('tag_two', response.data)
        response = self.client.get('/user/Admin?tag_disable=1', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        # get something with prev_url
        response = self.client.get('/user/Admin?tag=tag_one&prev_url=/article', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)
        self.assertNotIn('无标签', response.data)
        response = self.client.get('/user/Admin?category=test&prev_url=/article', follow_redirects=True)
        self.assertIn('article_title', response.data)
        self.assertIn('tag_one', response.data)

    def test_follow(self):
        self.login(username='Admin', password='1234')
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

    def test_edit_profile(self):
        self.login(username='user', password='1234')
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

    def test_message(self):
        self.login(username='user', password='1234')
        response = self.client.get(url_for('main.dialogues'))
        self.assertIn('系统消息', response.data)
        response = self.client.post(url_for('main.dialogues', dialogue_id=1), data={
            'content': 'test chat'
        }, follow_redirects=True)
        self.assertIn('test chat', response.data)
        self.assertNotIn('没有聊天记录', response.data)
        self.logout()
        self.login(username='Admin', password='1234')
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
        self.login(username='user', password='1234')
        response = self.client.get(url_for('main.new_dialogue', username='tester2'), follow_redirects=True)
        self.assertIn('tester2', response.data)

    def test_users(self):
        # worry user
        self.login(username='user', password='1234')
        response = self.client.get(url_for('admin_manager.users'))
        self.assertIn('Forbidden', response.data)
        self.logout()
        # right user
        self.login(username='Admin', password='1234')
        response = self.client.get(url_for('admin_manager.users'))
        self.assertIn('tester', response.data)
        self.assertIn('Admin', response.data)
        # edit profile
        response = self.client.get(url_for('admin_manager.edit_profile_admin', user_id=2))
        self.assertIn('user@CodeBlog.com', response.data)
        response = self.client.post(url_for('admin_manager.edit_profile_admin', user_id=2), data={
            'email': 'Admin@CodeBlog.com',
            'username': 'Admin',
            'confirmed': True,
            'role': 1,
            'name': '',
            'location': '',
            'about_me': ''
        }, follow_redirects=True)
        self.assertIn('邮箱地址已被使用', response.data)
        self.assertIn('用户名已被使用', response.data)
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
            'email': 'Admin@CodeBlog.com',
            'username': 'Admin',
            'confirmed': True,
            'role': 1,
            'name': '',
            'location': '',
            'about_me': ''
        }, follow_redirects=True)
        self.assertIn('邮箱地址已被使用', response.data)
        self.assertIn('用户名已被使用', response.data)
        response = self.client.post(url_for('admin_manager.edit_profile_admin'), data={
            'email': 'tester@CodeBlog.com',
            'username': 'tester',
            'confirmed': True,
            'role': 1,
            'name': '',
            'location': '',
            'about_me': ''
        }, follow_redirects=True)
        self.assertIn('用户创建成功', response.data)
        self.assertIn('tester', response.data)

    def test_moderate(self):
        self.login(username='Admin', password='1234')
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

    def test_categories(self):
        self.login(username='Admin', password='1234')
        response = self.client.get(url_for('admin_manager.categories'))
        self.assertIn('所有栏目', response.data)
        self.assertIn('None', response.data)
        response = self.client.post(url_for('admin_manager.categories'), data={
            'name': 'other',
            'parent': 1
        }, follow_redirects=True)
        self.assertIn('other', response.data)
        self.client.get(url_for('admin_manager.categories', category_id=2))
        response = self.client.post(url_for('admin_manager.categories', category_id=2), data={
            'name': 'None',
            'parent': 1
        }, follow_redirects=True)
        self.assertIn('已有同名的栏目', response.data)
        response = self.client.post(url_for('admin_manager.categories', category_id=2), data={
            'name': '测试',
            'parent': 1
        }, follow_redirects=True)
        self.assertIn('测试', response.data)
        response = self.client.get('/admin_manager/categories/delete/2', follow_redirects=True)
        self.assertNotIn('测试', response.data)

    def test_articles(self):
        self.login(username='Admin', password='1234')
        self.new_post()
        response = self.client.get(url_for('admin_manager.articles'))
        self.assertIn('所有博文', response.data)
        self.assertIn('summary', response.data)
        post = Post.query.first()
        response = self.client.get('/delete/post/%s?next=/admin_manager/articles' % post.id, follow_redirects=True)
        self.assertIn('所有博文', response.data)
        self.assertNotIn('summary', response.data)

    def test_tags(self):
        self.login(username='Admin', password='1234')
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


