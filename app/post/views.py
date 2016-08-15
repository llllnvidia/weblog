# -*- coding:utf-8 -*-
from flask import flash, redirect, url_for, request, current_app, render_template, abort
from flask_login import current_user, login_required

from . import post
from .forms import ArticleForm, CommentForm
from app.models.account import Permission
from app.models.post import Post, Comment, Category, Tag


@post.app_template_filter('markdown')
def txt_to_html(txt):
    from markdown import markdown
    return markdown(text=txt)


@post.route('/article/<int:post_id>', methods=['GET', 'POST'])
def article(post_id):
    prev_url = request.args.get('prev_url', '')
    post_show = Post.query.get_or_404(post_id)
    if post_show.is_draft and (current_user != post_show.author and not current_user.is_moderator()):
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
    return render_template('post/article.html', posts=[post_show], form=form, prev_url=prev_url,
                           comments=comments, pagination=pagination, page=page)


@post.route('/new/article', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if request.method == 'POST' and form.validate():
        post_new = Post(body=request.form['editor-markdown-doc'], title=form.title.data,
                        author=current_user,
                        summary=form.summary.data,
                        is_draft=form.is_draft.data,
                        category=Category.query.filter_by(id=form.category.data).first())
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
        current_app.logger.info('新文章 %s|%s', post_new.title, post_new.author.username)
        flash('发文成功！')
        return redirect(url_for('post.article', post_id=post_new.id))
    return render_template('post/editor.html', form=form)


@post.route('/edit/article/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_article(post_id):
    post_edit = Post.query.get_or_404(post_id)
    if current_user != post_edit.author and \
            not current_user.can(Permission.MODERATE_COMMENTS):
        abort(403)
    form = ArticleForm(category=post_edit.category.id)
    if request.method == 'POST' and form.validate():
        post_edit.title = form.title.data
        post_edit.body = request.form['editor-markdown-doc']
        post_edit.summary = form.summary.data
        post_edit.category = Category.query.filter_by(id=form.category.data).first()
        post_edit.is_draft = form.is_draft.data
        tags = [tag.strip() for tag in form.tags.data.split(',')] if form.tags.data else None
        if tags:
            post_tags = [tag for tag in post_edit.tags]
            for tag in post_tags:
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
            tags_delete = [tag for tag in post_edit.tags]
            for tag in tags_delete:
                post_edit.not_tag(tag)
        post_edit.ping()
        post_edit.save()
        current_app.logger.info('修改文章 %s|%s by %s', post_edit.title,
                                post_edit.author.username, current_user.username)
        flash('该文章已修改。')
        return redirect(url_for('post.article', post_id=post_id))
    if request.method == 'POST':
        post_body = request.form['editor-markdown-doc']
    else:
        form.title.data = post_edit.title
        form.summary.data = post_edit.summary
        form.is_draft.data = post_edit.is_draft
        post_body = post_edit.body
        form.tags.data = ','.join([str(tag.content) for tag in post_edit.tags])
    return render_template('post/editor.html', form=form, post=post_edit, post_body=post_body)


@post.route('/delete/post/<int:post_id>')
@login_required
def delete_post(post_id):
    next_url = request.args.get('next', '')
    post_delete = Post.query.get_or_404(post_id)
    if current_user != post_delete.author and \
            not current_user.can(0x0f):
        abort(403)
    else:
        current_app.logger.info('删除文章 %s|%s by %s', post_delete.title,
                                post_delete.author.username, current_user.username)
        post_delete.delete()
        flash('已删除！')
    if next_url:
        return redirect(next_url)
    else:
        return redirect(url_for('main.neighbourhood'))
