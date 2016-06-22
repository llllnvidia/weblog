# -*- coding: utf-8 -*-
from datetime import date

from flask import render_template, redirect, url_for, current_app, flash, \
    request, abort, make_response
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from flask_sqlalchemy import get_debug_queries

from app.models.account import Permission, User
from app.models.message import Dialogue
from app.models.post import Post, Category, Tag
from . import main
from .forms import EditProfileForm, ChatForm
from ..decorators import permission_required


@main.after_app_request
def after_request(response):
    for query_inspected in get_debug_queries():
        if query_inspected.duration >= current_app.config['DB_QUERY_TIMEOUT']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %s\nContext: %s\n' %
                (query_inspected.statement, query_inspected.parameters,
                 query_inspected.duration, query_inspected.context)
            )
    return response


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/neighbourhood', methods=['GET'])
def neighbourhood():
    categories_list = Category.query.filter_by(parent_id=1).all()
    tags = Tag.query.all()

    prev_url = request.args.get('prev_url', '')
    page = request.args.get('page', 1, type=int)
    cur_category = request.args.get('category', None)
    cur_category_cookie = request.cookies.get('category', None)
    category_disable = request.args.get('category_disable', None)
    cur_tag = request.args.get('tag', None)
    cur_tag_cookie = request.cookies.get('tags', '')
    tag_disable = request.args.get('tag_disable', None)
    cur_key = request.args.get('key', None)
    cur_key_cookie = request.cookies.get('key', None)
    key_disable = request.args.get('key_disable', None)
    show_talk = request.args.get('show_talk', None, type=int)
    show_talk_cookie = request.cookies.get('show_talk', None, type=int)
    show_followed = request.args.get('show_followed', None, type=int)
    show_followed_cookie = request.cookies.get('show_followed', None, type=int)

    # 处理从post.article栏目&标签跳转
    if prev_url:
        if cur_category:
            resp = make_response(redirect(url_for('main.neighbourhood', category=cur_category)))
        elif cur_tag:
            resp = make_response(redirect(url_for('main.neighbourhood', tag=cur_tag)))
        resp.set_cookie('show_talk', '', path=url_for('main.neighbourhood'), max_age=0)
        resp.set_cookie('tags', '', path=url_for('main.neighbourhood'), max_age=0)
        resp.set_cookie('category', '', path=url_for('main.neighbourhood'), max_age=0)
        resp.set_cookie('key', '', path=url_for('main.neighbourhood'), max_age=0)
        return resp

    # show_followed
    if show_followed is None and current_user.is_authenticated:
        show_followed = show_followed_cookie
    if show_followed and current_user.is_authenticated:
        if not show_followed_cookie:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_followed', '1', path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query_category_count = query = current_user.followed_posts.filter(Post.is_draft==False)
    else:
        if show_followed_cookie:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_followed', '', path=url_for('main.neighbourhood'), max_age=0)
            return resp
        query_category_count = query = Post.query.filter(Post.is_draft==False)

    # show_talk
    if not show_talk and not category_disable:
        show_talk = show_talk_cookie
    if show_talk:
        if not show_talk_cookie:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('tags', '', path=url_for('main.neighbourhood'), max_age=0)
            resp.set_cookie('show_talk', '1', path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        elif show_talk_cookie and cur_category:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_talk', '', path=url_for('main.neighbourhood'), max_age=0)
            resp.set_cookie('tags', '', path=url_for('main.neighbourhood'), max_age=0)
            resp.set_cookie('category', cur_category, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query = query.filter(Post.is_article == False)

    # category
    if not cur_category and not show_talk_cookie and not category_disable:
        cur_category = cur_category_cookie
    if cur_category:
        if not cur_category_cookie or cur_category_cookie != cur_category:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('tags', '', path=url_for('main.neighbourhood'), max_age=0)
            resp.set_cookie('category', cur_category, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query = Category.query.filter_by(name=cur_category).first().posts_query(query)
    if category_disable:
        resp = make_response(redirect(url_for('main.neighbourhood')))
        resp.set_cookie('tags', '', path=url_for('main.neighbourhood'), max_age=0)
        resp.set_cookie('category', '', path=url_for('main.neighbourhood'), max_age=0)
        resp.set_cookie('show_talk', '', path=url_for('main.neighbourhood'), max_age=0)
        return resp
    # tag
    cur_tags = cur_tag_cookie.split(',')
    if cur_tag:
        if cur_tag not in cur_tags:
            cur_tags.append(cur_tag)
            cur_tags = ','.join(cur_tags)
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('tags', cur_tags, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        elif cur_tag in cur_tags:
            cur_tags.remove(cur_tag)
            cur_tags = ','.join(cur_tags)
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('tags', cur_tags, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
    elif not tag_disable:
        for tag in cur_tags:
            if tag:
                query = Tag.query.filter_by(content=tag).first().posts_query(query)
    if tag_disable:
        resp = make_response(redirect(url_for('main.neighbourhood')))
        resp.set_cookie('tags', '', path=url_for('main.neighbourhood'), max_age=0)
        return resp

    # key
    if not cur_key and not key_disable:
        cur_key = cur_key_cookie
    if cur_key:
        if cur_key_cookie != cur_key:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('key', cur_key, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query = query.filter(Post.body.contains(cur_key) | Post.title.contains(cur_key) |
                             Post.summary.contains(cur_key))
    if key_disable:
        resp = make_response(redirect(url_for('main.neighbourhood')))
        resp.set_cookie('key', '', path=url_for('main.neighbourhood'), max_age=0)
        return resp

    # query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('neighbourhood.html', time=date(2016, 5, 6), User=User, posts=posts,
                           categories=categories_list, tags=tags, cur_tags=cur_tags,
                           cur_category=cur_category, show_talk=show_talk, key=cur_key,
                           show_followed=show_followed, query_category_count=query_category_count,
                           query_tag_count=query, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user_showed = User.query.filter_by(username=username).first()
    if user_showed is None:
        abort(404)
    query_category_count = query = user_showed.posts.filter_by(is_draft=False)
    categories_list = Category.query.filter_by(parent_id=1).all()
    tags = Tag.query.all()

    prev_url = request.args.get('prev_url', '')
    page = request.args.get('page', 1, type=int)
    cur_category = request.args.get('category', None)
    cur_category_cookie = request.cookies.get('category', None)
    category_disable = request.args.get('category_disable', None)
    cur_tag = request.args.get('tag', None)
    cur_tag_cookie = request.cookies.get('tags', '')
    tag_disable = request.args.get('tag_disable', None)
    cur_key = request.args.get('key', None)
    cur_key_cookie = request.cookies.get('key', None)
    key_disable = request.args.get('key_disable', None)
    show_talk = request.args.get('show_talk', None, type=int)
    show_talk_cookie = request.cookies.get('show_talk', None, type=int)

    # 处理从post.article栏目&标签跳转
    if prev_url:
        if cur_category:
            resp = make_response(redirect(url_for('main.user', username=username, category=cur_category)))
        elif cur_tag:
            resp = make_response(redirect(url_for('main.user', username=username, tag=cur_tag)))
        resp.set_cookie('show_talk', '', path=url_for('main.user', username=username), max_age=0)
        resp.set_cookie('tags', '', path=url_for('main.user', username=username), max_age=0)
        resp.set_cookie('category', '', path=url_for('main.user', username=username), max_age=0)
        resp.set_cookie('key', '', path=url_for('main.user', username=username), max_age=0)
        return resp

    # show_talk
    if not show_talk and not category_disable:
        show_talk = show_talk_cookie
    if show_talk:
        if not show_talk_cookie:
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('tags', '', path=url_for('main.user', username=username), max_age=0)
            resp.set_cookie('show_talk', '1', path=url_for('main.user', username=username), max_age=60 * 3)
            return resp
        elif show_talk_cookie and cur_category:
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('show_talk', '', path=url_for('main.user', username=username), max_age=0)
            resp.set_cookie('tags', '', path=url_for('main.user', username=username), max_age=0)
            resp.set_cookie('category', cur_category, path=url_for('main.user', username=username), max_age=60 * 3)
            return resp
        query = query.filter(Post.is_article == False)

    # category
    if not cur_category and not show_talk_cookie and not category_disable:
        cur_category = cur_category_cookie
    if cur_category:
        if not cur_category_cookie or cur_category_cookie != cur_category:
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('category', cur_category, path=url_for('main.user', username=username), max_age=60 * 3)
            resp.set_cookie('tags', '', path=url_for('main.user', username=username), max_age=0)
            return resp
        query = Category.query.filter_by(name=cur_category).first().posts_query(query)
    if category_disable:
        resp = make_response(redirect(url_for('main.user', username=username)))
        resp.set_cookie('category', '', path=url_for('main.user', username=username), max_age=0)
        resp.set_cookie('tags', '', path=url_for('main.user', username=username), max_age=0)
        resp.set_cookie('show_talk', '', path=url_for('main.user', username=username), max_age=0)
        return resp
    # tag
    cur_tags = cur_tag_cookie.split(',')
    if cur_tag:
        if cur_tag not in cur_tags:
            cur_tags.append(cur_tag)
            cur_tags = ','.join(cur_tags)
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('tags', cur_tags, path=url_for('main.user', username=username), max_age=60 * 3)
            return resp
        elif cur_tag in cur_tags:
            cur_tags.remove(cur_tag)
            cur_tags = ','.join(cur_tags)
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('tags', cur_tags, path=url_for('main.user', username=username), max_age=60 * 3)
            return resp
    elif not tag_disable:
        for tag in cur_tags:
            if tag:
                query = Tag.query.filter_by(content=tag).first().posts_query(query)
    if tag_disable:
        resp = make_response(redirect(url_for('main.user', username=username)))
        resp.set_cookie('tags', '', path=url_for('main.user', username=username), max_age=0)
        return resp

    # key
    if not cur_key and not key_disable:
        cur_key = cur_key_cookie
    if cur_key:
        if cur_key_cookie != cur_key:
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('key', cur_key, path=url_for('main.user', username=username), max_age=60 * 3)
            return resp
        query = query.filter(Post.body.contains(cur_key) | Post.title.contains(cur_key) |
                             Post.summary.contains(cur_key))
    if key_disable:
        resp = make_response(redirect(url_for('main.user', username=username)))
        resp.set_cookie('key', '', path=url_for('main.user', username=username), max_age=0)
        return resp

    # query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user_showed, posts=posts, query_category_count=query_category_count,
                           tags=tags, query_tag_count=query,
                           cur_tags=cur_tags, cur_category=cur_category, show_talk=show_talk, key=cur_key,
                           categories=categories_list, pagination=pagination)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user_follow = User.query.filter_by(username=username).first()
    if not user_follow:
        abort(404)
    if current_user.is_following(user_follow):
        flash('你已经关注了%s。' % username)
        return redirect(url_for('.user', username=username))
    current_user.follow(user_follow)
    user_follow.get_message_from_admin(content=u'你有一个新粉丝。', link_id=current_user.username, link_type='user')
    flash('你关注了%s。' % username)
    return redirect(url_for('.user', username=username))


@main.route('/not_follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def not_follow(username):
    user_not_follow = User.query.filter_by(username=username).first()
    if not user_not_follow:
        abort(404)
    if current_user.is_following(user_not_follow):
        current_user.not_follow(user_not_follow)
        user_not_follow.get_message_from_admin(content=u'你失去了一位粉丝。', link_id=current_user.username, link_type='user')
        flash('你取消了对%s的关注。' % username)
    else:
        flash('你没有关注过%s。' % username)
        return redirect(url_for('.user', username=username))
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user_show = User.query.filter_by(username=username).first()
    if user_show is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user_show.followers.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user_show, title="Followers of",
                           endpoint='.followers', pagination=pagination, follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user_showed = User.query.filter_by(username=username).first()
    if user_showed is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user_showed.followed.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user_showed, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        current_user.save()
        flash('你的资料已修改。')
        return redirect(url_for('main.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/dialogues/<int:dialogue_id>', methods=('GET', 'POST'))
@main.route('/dialogues')
@login_required
def dialogues(dialogue_id=None):
    dialogue_list = current_user.dialogues
    if dialogue_id:
        delete_true = request.args.get('delete_true', False, type=bool)
        dialogue = Dialogue.query.get_or_404(dialogue_id)
        if not dialogue.is_joining(current_user) or not dialogue.get_gallery(current_user).show:
            abort(404)
        if delete_true:
            dialogue = dialogue.get_gallery(current_user)
            dialogue.show = False
            dialogue.save()
            return redirect(url_for('main.dialogues'))
        dialogue.update_chats(current_user)     # 更新gallery.count
        current_user.ping()     # 更新current_user.new_messages_count
        form = ChatForm()
        page = request.args.get('page', 1, type=int)
        pagination = dialogue.chats.filter_by().paginate(
            page, per_page=current_app.config['DIALOGUE_PER_PAGE'],
            error_out=False)
        chats = pagination.items
        if form.validate_on_submit():
            dialogue.new_chat(author=current_user, content=form.content.data)
            flash('消息发送成功。')
            return redirect(url_for('main.dialogues', dialogue_id=dialogue_id) + '?page=' + str(pagination.pages))
        return render_template('message/dialogues.html', form=form, dialogues=dialogue_list, dialogue=dialogue,
                               chats=chats, pagination=pagination)
    else:
        return render_template('message/dialogues.html', dialogues=dialogue_list)


@main.route('/dialogues/new/<username>', methods=('GET', 'POST'))
@login_required
def new_dialogue(username):
    user_visit = User.query.filter_by(username=username).first()
    if Dialogue.is_together(user_visit, current_user):
        dialogue = Dialogue.get_dialogue(user_visit, current_user)
        gallery = dialogue.get_gallery(current_user)
        gallery.show = True
        gallery.save()
        return redirect(url_for('main.dialogues', dialogue_id=dialogue.id))
    else:
        dialogue = Dialogue(current_user, user_visit)
        return redirect(url_for('main.dialogues', dialogue_id=dialogue.id))


@main.route('/forbidden')
def forbidden():
    abort(403)


@main.route('/page_not_found')
def page_not_found():
    abort(404)


@main.route('/internal_server_error')
def internal_server_error():
    abort(500)


@main.route('/shutdown')
def server_shutdown():
    if not current_app.config['TESTING']:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'
