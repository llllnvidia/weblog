# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from flask.ext.pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import Required, Length, Email, Regexp
from wtforms import ValidationError
from ..models import Role, User

class EditProfileForm(Form):
    name = StringField('真实姓名',validators=[Length(0,64)])
    location = StringField('居住地',validators=[Length(0,64)])
    about_me = TextAreaField('个人简介')
    submin = SubmitField('提交')

class EditProfileAdminForm(Form):
    email = StringField('Email',validators=[Required(), Length(0,64), Email(message="请输入合法的邮箱地址。")])
    username = StringField('用户名',validators=[Required(), Length(0,64)])
    confirmed = BooleanField('邮箱认证')
    role = SelectField('身份',coerce=int)
    name = StringField('真实姓名',validators=[Length(0,64)])
    location = StringField('居住地',validators=[Length(0,64)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('提交')

    def __init__(self,user,*args,**kwargs):
        super(EditProfileAdminForm,self).__init__(*args,**kwargs)
        self.role.choices = [(role.id,role.name) 
                              for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self,field):
        if field.data != self.user.email and\
               User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已被使用')

class ArticleForm(Form):
    title = StringField('标题')
    body = PageDownField("", validators=[Required()])
    submit = SubmitField('发表')

class TalkForm(Form):
    body = StringField("",validators=[Required()])
    submit = SubmitField("说一说")

class CommentForm(Form):
    body = StringField('',validators=[Required(),Length(1,200,message="太长了。")])
    submit = SubmitField('提交')