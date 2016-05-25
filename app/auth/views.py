# -*- coding: utf-8 -*-

from flask import render_template, redirect, request, url_for, flash
from flask.ext.login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangePasswordForm, PasswordResetRequestForm, \
    PasswordResetForm
from ..email import send_email
from datetime import datetime


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('无效的用户名或密码')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已注销')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data,
                    member_since=datetime.utcnow())
        user.save()
        token = user.generate_confirmation_token()
        send_email(user.email, '账户确认',
                   'auth/email/confirm', user=user, token=token)
        flash('一封包含身份确认链接的邮件已发往你的邮箱。')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint[:5] != 'auth.':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        current_user.confirmed = True
        current_user.save()
        flash('已确认你的身份，欢迎加入我们。')
    else:
        flash('确认链接非法或已过期。')
    return redirect(url_for('main.index'))


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '账户确认',
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的包含身份确认链接的邮件已发往你的邮箱。')
    return redirect(url_for('main.index'))


@auth.route('/reset/email')
@login_required
def send_confirmation_email():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '账户确认',
               'auth/email/email_change_confirm', user=current_user, token=token)
    flash("确认邮件已发送，请确认。")
    return redirect(url_for('main.edit_profile', username=current_user.username))


@auth.route('/reset/email/<token>', methods=['GET', 'POST'])
@login_required
def email_change_confirm(token):
    form = ChangeEmailForm()
    if form.validate_on_submit() and current_user.confirm(token):
        current_user.email = form.email.data
        current_user.confirmed = False
        current_user.save()
        flash('修改成功。')
        token = current_user.generate_confirmation_token()
        send_email(current_user.email, '账户确认',
                   'auth/email/confirm', user=current_user, token=token)
        flash('一封包含身份确认链接的邮件已发往你的邮箱。')
        return redirect(url_for('main.index'))
    if not current_user.confirm(token):
        flash('确认链接非法或已过期。')
        return redirect(url_for('main.index'))
    return render_template('auth/change_email.html', form=form)


@auth.route('user/PasswordChange/', methods=['GET', 'POST'])
@login_required
def password_change():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            current_user.save()
            flash('修改成功。')
            return redirect(url_for('main.user', username=current_user.username))
        else:
            flash('请输入正确的密码')
            return render_template('auth/change_password.html', form=form)
    return render_template('auth/change_password.html', form=form)


@auth.route('/reset/password', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            send_email(user.email, '密码重设',
                       'auth/email/reset_password',
                       user=user, token=token,
                       next=request.args.get('next'))
        flash('一封含有重设密码的链接已发给你，请注意查收。')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/password/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            return redirect(url_for('main.index'))
        if user.reset_password(token, form.password.data):
            flash('你的密码已重设。')
            return redirect(url_for('auth.login'))
        else:
            flash('重设失败。')
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)
