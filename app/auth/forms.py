# -*- coding: utf-8 -*-

from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo

from app.models.account import User


class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message="请输入合法的邮箱地址。")])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登陆')


class RegistrationForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message="请输入合法的邮箱地址。")])
    username = StringField('用户名', validators=[DataRequired(), Length(1, 64)])
    password = PasswordField('密码', validators=[DataRequired(),
                                                 EqualTo('password2', message='两个密码必须相同。')])
    password2 = PasswordField('密码确认', validators=[DataRequired()])
    submit = SubmitField('注册')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email已被占用。')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被占用。')


class EmailForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message="请输入合法的邮箱地址。")])
    submit = SubmitField('确认')


class ChangeEmailForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message="请输入合法的邮箱地址。")])
    submit = SubmitField('更改')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email已被占用。')


class ChangePasswordForm(Form):
    old_password = PasswordField('旧密码', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired(),
                                                 EqualTo('password2', message='两个密码必须相同。')])
    password2 = PasswordField('密码确认', validators=[DataRequired()])
    submit = SubmitField('更改')


class PasswordResetRequestForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message="请输入合法的邮箱地址。")])
    submit = SubmitField('重设密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('无效的账号。')


class PasswordResetForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email(message="请输入合法的邮箱地址。")])
    password = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('password2', message='两个密码必须一样。')])
    password2 = PasswordField('新密码确认', validators=[DataRequired()])
    submit = SubmitField('重设密码')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('无效的账号。')
