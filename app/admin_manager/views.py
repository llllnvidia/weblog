# -*- coding: utf-8 -*-
from flask import flash, redirect, url_for, render_template, request, current_app
from flask_login import login_required

from app.decorators import admin_required, permission_required
from . import admin_manager
from .forms import EditProfileAdminForm, CategoryForm
from app.models.account import User, Role, Permission
from app.models.post import Comment, Category, Post, Tag


@admin_manager.route('/new/profile', methods=['GET', 'POST'])
@admin_manager.route('/edit/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id=None):
    if user_id:
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
            return redirect(url_for('admin_manager.users'))
        form.email.data = user_edited.email
        form.username.data = user_edited.username
        form.confirmed.data = user_edited.confirmed
        form.role.data = user_edited.role_id
        form.name.data = user_edited.name
        form.location.data = user_edited.location
        form.about_me.data = user_edited.about_me
    else:
        form = EditProfileAdminForm()
        if form.validate_on_submit():
            new_user = User(email=form.email.data,
                            username=form.username.data,
                            confirmed=form.confirmed.data,
                            role_id=form.role.data,
                            name=form.name.data,
                            location=form.location.data,
                            about_me=form.about_me.data,)
            new_user.save()
            flash('用户创建成功。')
            return redirect(url_for('admin_manager.users'))
    return render_template('admin_manager/edit_profile_admin.html', form=form)


@admin_manager.route('/comments')
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


@admin_manager.route('/comments/enable/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = False
    comment.save()
    flash("解禁成功")
    return redirect(url_for('admin_manager.moderate',
                            id=comment.post_id, page=request.args.get('page', 1, type=int)))


@admin_manager.route('/comments/disable/<int:comment_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    comment.disabled = True
    comment.save()
    flash("禁止显示")
    return redirect(url_for('admin_manager.moderate',
                            id=comment.post_id, page=request.args.get('page', 1, type=int)))


@admin_manager.route('/users')
@login_required
@permission_required(0x0f)
def users():
    page = request.args.get('page', 1, type=int)
    pagination = User.query.order_by(User.last_seen.desc()).paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    users_list = pagination.items
    return render_template('admin_manager/users.html', pagination=pagination, users=users_list)


@admin_manager.route('/users/delete/<int:user_id>')
@login_required
@permission_required(Permission.ADMINISTER)
def delete_user(user_id):
    user_deleted = User.query.get_or_404(user_id)
    user_deleted.delete()
    flash('已删除！')
    return redirect(url_for('admin_manager.users'))


@admin_manager.route('/categories/edit/<int:category_id>', methods=["GET", "POST"])
@admin_manager.route('/categories', methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def categories(category_id=None):
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.filter_by().paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    categories_list = pagination.items
    if category_id:
        category = Category.query.filter_by(id=category_id).first()
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            category.name = form.name.data
            category.save()
            flash("已修改")
            return redirect(url_for('admin_manager.categories', page=page, form=form))
        form.name.data = category.name
        form.parent.choices = [(category.parent_id,
                                Category.query.filter_by(id=category.parent_id).first().name)]
    else:
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            new_category = Category(form.name.data, Category.query.filter_by(id=form.parent.data).first())
            new_category.save()
            flash("已添加")
            return redirect(url_for('admin_manager.categories', page=page, form=form))
    return render_template('admin_manager/categories.html', form=form, pagination=pagination,
                           categories=categories_list)


@admin_manager.route('/categories/delete/<int:category_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    category.delete()
    flash("已删除")
    return redirect(url_for('admin_manager.categories'))


@admin_manager.route('/talks', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def talks():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(is_article=False).order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    talks_list = pagination.items
    return render_template('admin_manager/posts.html', title='所有吐槽', talks=talks_list, pagination=pagination)


@admin_manager.route('/articles', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def articles():
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(is_article=True).order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    articles_list = pagination.items
    return render_template('admin_manager/posts.html', title='所有博文', articles=articles_list, pagination=pagination)


@admin_manager.route('/tags', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def tags():
    page = request.args.get('page', 1, type=int)
    pagination = Tag.query.paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    tags_list = pagination.items
    return render_template('admin_manager/tags.html', tags=tags_list, pagination=pagination)


@admin_manager.route('/delete/tag/<int:tag_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_tag(tag_id):
    tag_delete = Tag.query.get_or_404(tag_id)
    tag_delete.delete()
    flash('已删除！')
    return redirect(url_for('admin_manager.tags'))
