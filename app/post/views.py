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
    post_show = Post.query.get_or_404(post_id)
    if not post_show.is_article:
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("请先登录")
            return redirect(url_for('auth.login', next=str(request.url)))
        comment = Comment(body=form.body.data,
                          post=post_show,
                          author=current_user)
        post_show.author.get_message_from_admin(content=u'你收到了一条评论。', link_id=post_show.id, link_type='comment')
        comment.save()
        flash('你的评论已提交。')
        return redirect(url_for('post.article', post_id=post_show.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post_show.comments.count() - 1) / \
               current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post_show.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post/article.html', posts=[post_show], form=form,
                           comments=comments, pagination=pagination, page=page)


@post.route('/new/article', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if request.method == 'POST':
        post_new = Post(body=request.form['editor-markdown-doc'], title=form.title.data,
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
                post_new.tag(new_tag)
        post_new.ping()
        post_new.save()
        return redirect(url_for('post.article', post_id=post_new.id, page=-1))
    return render_template('post/editor.html', form=form, article=True)


@post.route('/edit/article/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_article(post_id):
    post_edit = Post.query.get_or_404(post_id)
    if current_user != post_edit.author and \
            not current_user.can(Permission.MODERATE_COMMENTS):
        abort(403)
    if post_edit.category:
        form = ArticleForm(category=post_edit.category.id)
    else:
        form = ArticleForm()
    if request.method == 'POST' and form.validate():
        post_edit.title = form.title.data
        post_edit.body = form.body.data
        post_edit.summary = form.summary.data
        post_edit.category = Category.query.filter_by(id=form.category.data).first()
        post_edit.is_article = True
        tags = [tag.strip() for tag in form.tags.data.split(',')] if form.tags.data else None
        if tags:
            for tag in post_edit.tags:
                if tag.content not in tags:
                    post_edit.not_tag(tag)
            for tag in tags:
                new_tag = Tag.query.filter_by(content=tag).first()
                if not new_tag:
                    new_tag = Tag(tag)
                    new_tag.save()
                if new_tag not in post_edit.tags:
                    post_edit.tag(new_tag)
        else:
            for tag in post_edit.tags:
                    post_edit.not_tag(tag)
        post_edit.ping()
        post_edit.save()
        flash('该文章已修改。')
        return redirect(url_for('post.article', post_id=post_id, page=-1))
    form.title.data = post_edit.title
    form.summary.data = post_edit.summary
    form.body.data = post_edit.body
    form.tags.data = ','.join([str(tag.content) for tag in post_edit.tags])
    return render_template('post/edit_post.html', form=form, article=True, post=post_edit)


@post.route('/delete/post/<int:post_id>')
@login_required
def delete_post(post_id):
    post_delete = Post.query.get_or_404(post_id)
    if current_user != post_delete.author and \
            not current_user.can(0x0f):
        abort(403)
    else:
        post_delete.delete()
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
