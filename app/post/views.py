# -*- coding:utf-8 -*-
from flask import flash, redirect, url_for, request, current_app, render_template, abort
from flask.ext.login import current_user, login_required

from . import post
from .forms import ArticleForm, TalkForm, CommentForm
from app.models.account import Permission
from app.models.post import Post, Comment, Category, Tag


@post.app_template_filter('markdown')
def txt_to_html(txt):
    from markdown import markdown
    return markdown(text=txt)


@post.route('/article/<int:post_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('post.article', post_id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post/article.html', posts=[post], form=form,
                           comments=comments, pagination=pagination, page=page)


@post.route('/new/article', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if request.method == 'POST' and form.validate():
        post = Post(body=form.body.data, title=form.title.data,
                    author=current_user,
                    summary=form.summary.data,
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
        return redirect(url_for('post.article', post_id=post.id, page=-1))
    return render_template('post/edit_post.html', form=form, article=True)


@post.route('/edit/article/<int:post_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('post.article', post_id=post_id, page=-1))
    form.title.data = post.title
    form.summary.data = post.summary
    form.body.data = post.body
    form.tags.data = ','.join([str(tag.content) for tag in post.tags])
    return render_template('post/edit_post.html', form=form, article=True, post=post)


@post.route('/delete-post/<int:post_id>')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author and \
            not current_user.can(0x0f):
        abort(403)
    else:
        post.delete()
        flash('已删除！')
        return redirect(url_for('main.neighbourhood'))


@post.route('/new/talk', methods=['GET', 'POST'])
@login_required
def new_talk():
    form = TalkForm()
    if form.validate_on_submit():
        talk = Post(body=form.body.data,
                    is_article=False,
                    author=current_user)
        talk.save()
        return redirect(url_for('main.neighbourhood'))
    return render_template('post/edit_post.html', form=form, article=False)


@post.route('/edit/talk/<int:post_id>', methods=['GET', 'POST'])
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
    return render_template('post/edit_post.html', form=form, is_new=int(post_id), article=False, post=talk)
