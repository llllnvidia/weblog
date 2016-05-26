# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from flask.ext.pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Length, Email
from wtforms import ValidationError
from ..models import Role, User, Category


class EditProfileForm(Form):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('居住地', validators=[Length(0, 64)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('提交')


class EditProfileAdminForm(Form):
    email = StringField('Email', validators=[DataRequired(), Length(0, 64), Email(message="请输入合法的邮箱地址。")])
    username = StringField('用户名', validators=[DataRequired(), Length(0, 64)])
    confirmed = BooleanField('邮箱认证')
    role = SelectField('身份', coerce=int)
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('居住地', validators=[Length(0, 64)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('提交')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用')


def validate_tag(self, field):
    if field.data.find('，') != -1:
        raise ValidationError('请使用英文逗号‘,’来分隔标签。')


class ArticleForm(Form):
    title = StringField('标题')
    body = PageDownField("", validators=[DataRequired()])
    tags = StringField('标签',validators=[validate_tag])
    category = SelectField("栏目", coerce=int)
    submit = SubmitField('发表')

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.category.choices = [(cg.id, cg.name) for cg in Category.query.all()]




class TalkForm(Form):
    body = TextAreaField("", validators=[DataRequired(), Length(1, 200, message="太长了。")])
    submit = SubmitField("说一说")


class CommentForm(Form):
    body = StringField('', validators=[DataRequired(), Length(1, 200, message="太长了。")])
    submit = SubmitField('提交')


class CategoryForm(Form):
    name = StringField('栏目名称', validators=[DataRequired(), Length(1, 10, message='太长了。')])
    parent = SelectField("父栏目", coerce=int)
    submit = SubmitField("提交")

    def __init__(self, *args, **kwargs):
        super(CategoryForm, self).__init__(*args, **kwargs)
        category = Category.query.filter(Category.name == 'None').first()
        choices = [(category.id, category.name)]
        if Category.query.filter(Category.parentid == 1).count():
            choices.extend([(cg.id, cg.name) for cg in Category.query.filter(Category.parentid == 1).all()])
        self.parent.choices = choices


class UploadImagesForm(Form):
    upload = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    submit = SubmitField("提交")