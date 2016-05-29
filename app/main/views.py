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


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/neighbourhood', methods=['GET'])
def neighbourhood():
    categorys = Category.query.filter_by(parentid=1).all()
    tags = Tag.query.all()
    page = request.args.get('page', 1, type=int)
    cur_category = request.args.get('category', None)
    cur_tag = request.args.get('tag', None)
    cur_key = request.args.get('key', None)
    show_talk = request.args.get('show_talk', None)
    show = request.args.get('show_followed', None)
    show_followed = request.cookies.get('show_followed', None)
    if show is None:
        show = show_followed
    if not current_user.is_authenticated:
        show = None
    if show:
        show = int(show)
        if show:
            if not show_followed or show_followed == '0':
                resp = make_response(redirect(url_for('main.neighbourhood')))
                resp.set_cookie('show_followed', '1', max_age=60 * 3)
                return resp
            query_show = query = current_user.followed_posts
        else:
            if not show_followed or show_followed == '1':
                resp = make_response(redirect(url_for('main.neighbourhood')))
                resp.set_cookie('show_followed', '0', max_age=60 * 3)
                return resp
            query_show = query = Post.query
    else:
        query_show = query = Post.query
    if show_talk:
        query = query.filter(Post.is_article == False)
    if cur_category:
        query = Category.query.filter_by(name=cur_category).first().posts_query(query)
    if cur_tag:
        query = Tag.query.filter_by(content=cur_tag).first().posts_query(query)
    if cur_key:
        query = query.filter(Post.body.contains(cur_key) | Post.title.contains(cur_key))
    if query:
        pagination = query.order_by(Post.timestamp.desc()).paginate(
            page, per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False)
        posts = pagination.items
        return render_template('neighbourhood.html', time=date(2016, 5, 6), User=User, posts=posts, cur_tag=cur_tag,
                               Post=Post, categorys=categorys, tags=tags, show_followed=show, query=query_show,
                               pagination=pagination)
    else:
        return render_template('neighbourhood.html', time=date(2016, 5, 6), User=User, cur_tag=cur_tag,
                               Post=Post, categorys=categorys, tags=tags, show_followed=show, query=query_show)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    query_show = query = user.posts.filter_by(is_article=True).order_by(Post.timestamp.desc())
    categorys = Category.query.filter_by(parentid=1).all()
    tags = Tag.query.all()
    page = request.args.get('page', 1, type=int)
    cur_category = request.args.get('category')
    cur_tag = request.args.get('tag')
    cur_key = request.args.get('key')
    if cur_category:
        query = Category.query.filter_by(name=cur_category).first().posts_query(query)
    if cur_tag:
        query = Tag.query.filter_by(content=cur_tag).first().posts_query(query)
    if cur_key:
        query = query.filter(Post.body.contains(cur_key) | Post.title.contains(cur_key))
    if query:
        pagination = query.paginate(
            page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
            error_out=False)
        posts = pagination.items
        return render_template('user.html', user=user, posts=posts, query=query_show, tags=tags, cur_tag=cur_tag,
                               categorys=categorys, pagination=pagination)
    else:
        return render_template('user.html', user=user, query=query_show, tags=tags, cur_tag=cur_tag,
                               categorys=categorys)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if current_user.is_following(user):
        flash('你已经关注了%s。' % username)
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('你关注了%s。' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if current_user.is_following(user):
        current_user.unfollow(user)
        flash('你取消了对%s的关注。' % username)
    else:
        flash('你没有关注过%s。' % username)
        return redirect(url_for('.user', username=username))
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination, follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
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


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        user.save()
        flash('资料已修改。')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile_admin.html', form=form, user=user)


@main.route('/article/<int:id>', methods=['GET', 'POST'])
def article(id):
    post = Post.query.get_or_404(id)
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
        comment.save()
        flash('你的评论已提交。')
        return redirect(url_for('main.article', id=post.id, page=-1))
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


@main.route('/new/article', methods=['GET','POST'])
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
        return redirect(url_for('main.article', id=post.id, page=-1))
    return render_template('edit_post.html', form=form, article=True)


@main.route('/edit/article/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    post = Post.query.get_or_404(id)
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
        post.category = Category.query.filter_by(id=form.category.data).first()
        post.is_article = True
        tags = [tag.strip() for tag in form.tags.data.split(',')] if form.tags.data else None
        if tags:
            for tag in post.tags:
                if tag.content not in tags:
                    post.untag(tag)
            for tag in tags:
                new_tag = Tag.query.filter_by(content=tag).first()
                if not new_tag:
                    new_tag = Tag(tag)
                    new_tag.save()
                if new_tag not in post.tags:
                    post.tag(new_tag)
        else:
            for tag in post.tags:
                    post.untag(tag)
        post.ping()
        post.save()
        flash('该文章已修改。')
        return redirect(url_for('main.article', id=id, page=-1))
    form.title.data = post.title
    form.body.data = post.body
    form.tags.data = ','.join([str(tag.content) for tag in post.tags])
    return render_template('edit_post.html', form=form, article=True, post=post)


@main.route('/delete-post/<int:id>')
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(0x0f):
        abort(403)
    else:
        post.delete()
        flash('已删除！')
        return redirect(url_for('.neighbourhood'))


@main.route('/comment')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('comments.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/comment/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    comment.save()
    flash("解禁成功")
    return redirect(url_for('main.moderate',
                            id=comment.post_id, page=request.args.get('page', 1, type=int)))


@main.route('/comment/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
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
    users = [{'id': item.id, 'user': item.username, 'name': item.name,
              'member_since': item.member_since, 'last_seen': item.last_seen}
             for item in pagination.items]
    return render_template('users.html', title="所有用户",
                           endpoint='.users', pagination=pagination, users=users)


@main.route('/users/delete/<int:id>')
@login_required
@permission_required(Permission.ADMINISTER)
def delete_user(id):
    user = User.query.get_or_404(id)
    user.delete()
    flash('已删除！')
    return redirect(url_for('main.users'))


@main.route('/categorys/edit/<int:id>', methods=["GET", "POST"])
@main.route('/categorys', methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def categorys(id=None):
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.filter_by().paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    categorys = list()
    for item in pagination.items:
        arg = {'id': item.id, 'name': item.name}
        if item.parentcategory:
            arg.update({'parentcategory': Category.query.filter_by(id=item.parentid).first().name})
        else:
            arg.update({'parentcategory': 'None'})
        if item.soncategorys:
            arg.update({'soncategorys': ' '.join([cg.name for cg in item.soncategorys])})
            arg.update({'count': item.posts_count()})
        else:
            arg.update({'soncategorys': 'None'})
            arg.update({'count': item.posts_count()})
        categorys.append(arg)
    if id:
        category = Category.query.filter_by(id=id).first()
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            category.name = form.name.data
            category.save()
            flash("已修改")
            return redirect(url_for('main.categorys', page=page, form=form))
        form.name.data = category.name
        form.parent.choices = [(category.parentid,
                                Category.query.filter_by(id=category.parentid).first().name)]
        return render_template('categorys.html', title="所有栏目", form=form,
                               endpoint='main.categorys', pagination=pagination, categorys=categorys)
    else:
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            new_category = Category(form.name.data, Category.query.filter_by(id=form.parent.data).first())
            new_category.save()
            flash("已添加")
            return redirect(url_for('main.categorys', page=page, form=form))
        return render_template('categorys.html', title="所有栏目", form=form,
                               endpoint='main.categorys', pagination=pagination, categorys=categorys)


@main.route('/categorys/delete/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_category(id):
    category = Category.query.filter_by(id=id).first()
    category.delete()
    flash("已删除")
    return redirect(url_for('main.categorys'))


@main.route('/new/talk', methods=['GET', 'POST'])
@login_required
def new_talk():
    form = TalkForm()
    if form.validate_on_submit():
        talk = Post(body=form.body.data,
                    is_article=False,
                    author=current_user._get_current_object())
        talk.save()
        return redirect(url_for('.neighbourhood', id=talk.id))
    return render_template('edit_post.html', form=form, article=False)


@main.route('/edit/talk/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_talk(id):
    talk = Post.query.get_or_404(id)
    form = TalkForm()
    if form.validate_on_submit():
        talk.body = form.body.data
        talk.ping()
        talk.save()
        flash("已修改。")
        return redirect(url_for('main.neighbourhood'))
    form.body.data = talk.body
    return render_template('edit_post.html', form=form, is_new=int(id), article=False, post=talk)


@main.route('/upload/images', methods=('GET', 'POST'))
@login_required
def upload_images():
    form = UploadImagesForm()
    if form.validate_on_submit():
        filename = form.upload.data.filename
        form.upload.data.save('C:/Users/NHT/PycharmProjects/codeblog/uploads/' + filename)
    else:
        filename = None
    return render_template('upload.html', form=form, filename=filename)


@main.route('/dialogues/<int:id>', methods=('GET', 'POST'))
@main.route('/dialogues')
@login_required
def dialogues(id=None):
    dialogue_list = current_user.dialogues
    if id:
        delete_true = request.args.get('delete_true', False, type=bool)
        dialogue = Dialogue.query.get_or_404(id)
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
        if form.validate_on_submit():
            dialogue.new_chat(author=current_user, content=form.content.data)
            dialogue.update_show()
            flash('消息发送成功。')
            return redirect(url_for('main.dialogues', id=id))
        pagination = dialogue.chats.filter_by().paginate(
            page, per_page=current_app.config['DIALOGUE_PER_PAGE'],
            error_out=False)
        chats = pagination.items
        return render_template('message/dialogues.html', form=form, dialogues=dialogue_list, dialogue=dialogue,
                               chats=chats, pagination=pagination)
    else:
        return render_template('message/dialogues.html', dialogues=dialogue_list)


@main.route('/dialogues/new/<username>', methods=('GET', 'POST'))
@login_required
def new_dialogue(username):
    user = User.query.filter_by(username=username).first()
    if Dialogue.is_together(user, current_user):
        dialogue = Dialogue.get_dialogue(user, current_user)
        gallery = dialogue.get_gallery(current_user)
        gallery.show = True
        gallery.save()
        return redirect(url_for('main.dialogues', id=dialogue.id))
    else:
        dialogue = Dialogue(current_user, user)
        return redirect(url_for('main.dialogues', id=dialogue.id))