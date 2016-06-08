# -*- coding: utf-8 -*-
from flask import flash, redirect, url_for, render_template, request, current_app
from flask.ext.login import login_required

from app.decorators import admin_required, permission_required
from . import admin_manager
from .forms import EditProfileAdminForm, CategoryForm
from app.models.account import User, Role, Permission
from app.models.post import Comment, Category


@admin_manager.route('/edit-profile/<int:user_id>', methods=['GET', 'POST'])
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
    return render_template('admin_manager/edit_profile_admin.html', form=form, user=user_edited)


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
    users_list = [{'id': item.id, 'user': item.username, 'name': item.name,
                   'member_since': item.member_since,
                   'last_seen': item.last_seen}for item in pagination.items]
    return render_template('admin_manager/users.html', title="所有用户",
                           endpoint='.users', pagination=pagination, users=users_list)


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
            return redirect(url_for('admin_manager.categories', page=page, form=form))
        form.name.data = category.name
        form.parent.choices = [(category.parent_id,
                                Category.query.filter_by(id=category.parent_id).first().name)]
        return render_template('admin_manager/categories.html', title="所有栏目", form=form,
                               endpoint='admin_manager.categories', pagination=pagination, categories=categories_list)
    else:
        form = CategoryForm()
        if request.method == 'POST' and form.validate():
            new_category = Category(form.name.data, Category.query.filter_by(id=form.parent.data).first())
            new_category.save()
            flash("已添加")
            return redirect(url_for('admin_manager.categories', page=page, form=form))
        return render_template('admin_manager/categories.html', title="所有栏目", form=form,
                               endpoint='admin_manager.categories', pagination=pagination, categories=categories_list)


@admin_manager.route('/categories/delete/<int:category_id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    category.delete()
    flash("已删除")
    return redirect(url_for('admin_manager.categories'))
