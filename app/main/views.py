# -*- coding: utf-8 -*-
from datetime import date

from flask import render_template, redirect, url_for, current_app, flash, \
    request, abort, make_response
from flask.ext.login import current_user, login_required

from app.models.post import Post, Comment, Category, Tag
from app.models.account import Role, Permission, User
from app.models.message import Dialogue
from . import main
from .forms import TalkForm, EditProfileForm, EditProfileAdminForm, CommentForm, ArticleForm, CategoryForm, \
    UploadImagesForm, ChatForm
from ..decorators import admin_required, permission_required


@main.app_template_filter('markdown')
def txt_to_html(txt):
    from markdown import markdown
    return markdown(text=txt)


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/neighbourhood', methods=['GET'])
def neighbourhood():
    categories_list = Category.query.filter_by(parent_id=1).all()
    tags = Tag.query.all()

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

    # show_followed
    if show_followed is None and current_user.is_authenticated:
        show_followed = show_followed_cookie
    if show_followed:
        if not show_followed_cookie:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_followed', '1', path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query_show = query = current_user.followed_posts
    else:
        if show_followed_cookie:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_followed', '0', path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query_show = query = Post.query

    # show_talk
    if not show_talk and not category_disable:
        show_talk = show_talk_cookie
    if show_talk:
        if not show_talk_cookie:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_talk', '1', path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        elif show_talk_cookie and cur_category:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('show_talk', '0', path=url_for('main.neighbourhood'), max_age=60 * 3)
            resp.set_cookie('category', cur_category, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query = query.filter(Post.is_article == False)

    # category
    if not cur_category and not show_talk_cookie and not category_disable:
        cur_category = cur_category_cookie
    if cur_category:
        if not cur_category_cookie or cur_category_cookie != cur_category:
            resp = make_response(redirect(url_for('main.neighbourhood')))
            resp.set_cookie('category', cur_category, path=url_for('main.neighbourhood'), max_age=60 * 3)
            return resp
        query = Category.query.filter_by(name=cur_category).first().posts_query(query)
    if category_disable:
        resp = make_response(redirect(url_for('main.neighbourhood')))
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
        query = query.filter(Post.body.contains(cur_key) | Post.title.contains(cur_key) | Post.summary.contains(cur_key))
    if key_disable:
        resp = make_response(redirect(url_for('main.neighbourhood')))
        resp.set_cookie('key', '', path=url_for('main.neighbourhood'), max_age=0)
        return resp

    # query
    if query:
        pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False)
        posts = pagination.items
        return render_template('neighbourhood.html', time=date(2016, 5, 6), User=User, posts=posts,
                               categories=categories_list, tags=tags, cur_tags=cur_tags,
                               cur_category=cur_category, show_talk=show_talk, key=cur_key,
                               show_followed=show_followed, query=query_show, pagination=pagination)
    else:
        return render_template('neighbourhood.html', time=date(2016, 5, 6), User=User,
                               categories=categories_list, tags=tags, cur_tags=cur_tags,
                               cur_category=cur_category, show_talk=show_talk, key=cur_key,
                               show_followed=show_followed, query=query_show)


@main.route('/user/<username>')
def user(username):
    user_showed = User.query.filter_by(username=username).first()
    if user_showed is None:
        abort(404)
    query_show = query = user_showed.posts.filter_by(is_article=True)
    categories_list = Category.query.filter_by(parent_id=1).all()
    tags = Tag.query.all()
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

    # show_talk
    if not show_talk and not category_disable:
        show_talk = show_talk_cookie
    if show_talk:
        if not show_talk_cookie:
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('show_talk', '1', path=url_for('main.user', username=username), max_age=60 * 3)
            return resp
        elif show_talk_cookie and cur_category:
            resp = make_response(redirect(url_for('main.user', username=username)))
            resp.set_cookie('show_talk', '0', path=url_for('main.user', username=username), max_age=60 * 3)
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
            return resp
        query = Category.query.filter_by(name=cur_category).first().posts_query(query)
    if category_disable:
        resp = make_response(redirect(url_for('main.user', username=username)))
        resp.set_cookie('category', '', path=url_for('main.user', username=username), max_age=0)
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
        query = query.filter(Post.body.contains(cur_key) | Post.title.contains(cur_key) | Post.summary.contains(cur_key))
    if key_disable:
        resp = make_response(redirect(url_for('main.user', username=username)))
        resp.set_cookie('key', '', path=url_for('main.user', username=username), max_age=0)
        return resp

    # query
    if query:
        pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
            error_out=False)
        posts = pagination.items
        return render_template('user.html', user=user_showed, posts=posts, query=query_show, tags=tags,
                               cur_tags=cur_tags, cur_category=cur_category, show_talk=show_talk, key=cur_key,
                               categories=categories_list, pagination=pagination)
    else:
        return render_template('user.html', user=user_showed, query=query_show, tags=tags,
                               cur_tags=cur_tags, cur_category=cur_category, show_talk=show_talk, key=cur_key,
                               categories=categories_list)


@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user_follow = User.query.filter_by(username=username).first()
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
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user_edited = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user_edited)
    if form.validate_on_submit():
        user_edited.email = form.email.data
        user_edited.username = form.username.data
        user_edited.confirmed = form.confirmed.data
        user_edited.role = Role.query.get(form.role.data)
        user_edited.name = form.name.data
        user_edited.location = form.location.data
        user_edited.about_me = form.about_me.data
        user_edited.save()
        flash('资料已修改。')
        return redirect(url_for('.user', username=user_edited.username))
    form.email.data = user_edited.email
    form.username.data = user_edited.username
    form.confirmed.data = user_edited.confirmed
    form.role.data = user_edited.role_id
    form.name.data = user_edited.name
    form.location.data = user_edited.location
    form.about_me.data = user_edited.about_me
    return render_template('edit_profile_admin.html', form=form, user=user_edited)


@main.route('/article/<int:post_id>', methods=['GET', 'POST'])
def article(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_article:
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("请先登录")
            return redirect(url_for('auth.login', next=str(request.url)))
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user)
        post.author.get_message_from_admin(content=u'你收到了一条评论。', link_id=post.id, link_type='comment')
        comment.save()
        flash('你的评论已提交。')
        return redirect(url_for('main.article', post_id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('article.html', posts=[post], form=form,
                           comments=comments, pagination=pagination, page=page)


@main.route('/new/article', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if request.method == 'POST' and form.validate():
        post = Post(body=form.body.data, title=form.title.data,
                    author=current_user,
                    is_article=True, category=Category.query.filter_by(id=form.category.data).first())
        tags = [tag.strip() for tag in form.tags.data.split(',')] if form.tags.data else None
        if tags:
            for tag in tags:
                new_tag = Tag.query.filter_by(content=tag).first()
                if not new_tag:
                    new_tag = Tag(tag)
                    new_tag.save()
                post.tag(new_tag)
        post.ping()
        post.save()
        return redirect(url_for('main.article', post_id=post.id, page=-1))
    return render_template('edit_post.html', form=form, article=True)


@main.route('/edit/article/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_article(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author and \
            not current_user.can(Permission.MODERATE_COMMENTS):
        abort(403)
    if post.category:
        form = ArticleForm(category=post.category.id)
    else:
        form = ArticleForm()
    if request.method == 'POST' and form.validate():
        post.title = form.title.data
        post.body = form.body.data
        post.summary = form.summary.data
        post.category = Category.query.filter_by(id=form.category.data).first()
        post.is_article = True
        tags = [tag.strip() for tag in form.tags.data.split(',')] if form.tags.data else None
        if tags:
            for tag in post.tags:
                if tag.content not in tags:
                    post.not_tag(tag)
            for tag in tags:
                new_tag = Tag.query.filter_by(content=tag).first()
                if not new_tag:
                    new_tag = Tag(tag)
                    new_tag.save()
                if new_tag not in post.tags:
                    post.tag(new_tag)
        else:
            for tag in post.tags:
                    post.not_tag(tag)
        post.ping()
        post.save()
        flash('该文章已修改。')
        return redirect(url_for('main.article', post_id=post_id, page=-1))
    form.title.data = post.title
    form.summary.data = post.summary
    form.body.data = post.body
    form.tags.data = ','.join([str(tag.content) for tag in post.tags])
    return render_template('edit_post.html', form=form, article=True, post=post)


@main.route('/delete-post/<int:post_id>')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author and \
            not current_user.can(0x0f):
        abort(403)
    else:
        post.delete()
        flash('已删除！')
        return redirect(url_for('.neighbourhood'))


@main.route('/comments')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('admin_manager/comments.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/comments/enable/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = False
    comment.save()
    flash("解禁成功")
    return redirect(url_for('main.moderate',
                            id=comment.post_id, page=request.args.get('page', 1, type=int)))


@main.route('/comments/disable/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = True
    comment.save()
    flash("禁止显示")
    return redirect(url_for('main.moderate',
                            id=comment.post_id, page=request.args.get('page', 1, type=int)))


@main.route('/users')
@login_required
@permission_required(0x0f)
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.last_seen.desc()).paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    users_list = [{'id': item.id, 'user': item.username, 'name': item.name,
                   'member_since': item.member_since,
                   'last_seen': item.last_seen}for item in pagination.items]
    return render_template('admin_manager/users.html', title="所有用户",
                           endpoint='.users', pagination=pagination, users=users_list)


@main.route('/users/delete/<int:user_id>')
@login_required
@permission_required(Permission.ADMINISTER)
def delete_user(user_id):
    user_deleted = User.query.get_or_404(user_id)
    user_deleted.delete()
    flash('已删除！')
    return redirect(url_for('main.users'))


@main.route('/categories/edit/<int:category_id>', methods=["GET", "POST"])
@main.route('/categories', methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def categories(category_id=None):
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.filter_by().paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    categories_list = list()
    for item in pagination.items:
        arg = {'id': item.id, 'name': item.name}
        if item.parent_category:
            arg.update({'parent_category': Category.query.filter_by(id=item.parent_id).first().name})
        else:
            arg.update({'parent_category': 'None'})
        if item.son_categories:
            arg.update({'son_categories': ' '.join([cg.name for cg in item.son_categories])})
            arg.update({'count': item.posts_count()})
        else:
            arg.update({'son_categories': 'None'})
            arg.update({'count': item.posts_count()})
        categories_list.append(arg)
    if category_id:
        category = Category.query.filter_by(id=category_id).first()
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            category.name = form.name.data
            category.save()
            flash("已修改")
            return redirect(url_for('main.categories', page=page, form=form))
        form.name.data = category.name
        form.parent.choices = [(category.parent_id,
                                Category.query.filter_by(id=category.parent_id).first().name)]
        return render_template('admin_manager/categories.html', title="所有栏目", form=form,
                               endpoint='main.categories', pagination=pagination, categories=categories_list)
    else:
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            new_category = Category(form.name.data, Category.query.filter_by(id=form.parent.data).first())
            new_category.save()
            flash("已添加")
            return redirect(url_for('main.categories', page=page, form=form))
        return render_template('admin_manager/categories.html', title="所有栏目", form=form,
                               endpoint='main.categories', pagination=pagination, categories=categories_list)


@main.route('/categories/delete/<int:category_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    category.delete()
    flash("已删除")
    return redirect(url_for('main.categories'))


@main.route('/new/talk', methods=['GET', 'POST'])
@login_required
def new_talk():
    form = TalkForm()
    if form.validate_on_submit():
        talk = Post(body=form.body.data,
                    is_article=False,
                    author=current_user)
        talk.save()
        return redirect(url_for('.neighbourhood'))
    return render_template('edit_post.html', form=form, article=False)


@main.route('/edit/talk/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_talk(post_id):
    talk = Post.query.get_or_404(post_id)
    form = TalkForm()
    if form.validate_on_submit():
        talk.body = form.body.data
        talk.ping()
        talk.save()
        flash("已修改。")
        return redirect(url_for('main.neighbourhood'))
    form.body.data = talk.body
    return render_template('edit_post.html', form=form, is_new=int(post_id), article=False, post=talk)


@main.route('/upload/images', methods=('GET', 'POST'))
@login_required
def upload_images():
    form = UploadImagesForm()
    if form.validate_on_submit():
        filename = form.upload.data.filename
        form.upload.data.save(current_app.config['IMG_PATH'] + filename)
    else:
        filename = None
    return render_template('upload.html', form=form, filename=filename)


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
        dialogue.update_chats(current_user)
        form = ChatForm()
        page = request.args.get('page', 1, type=int)
        pagination = dialogue.chats.filter_by().paginate(
            page, per_page=current_app.config['DIALOGUE_PER_PAGE'],
            error_out=False)
        chats = pagination.items
        if form.validate_on_submit():
            dialogue.new_chat(author=current_user, content=form.content.data)
            dialogue.update_show()
            dialogue.update_chats(current_user)
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