# -*- coding: utf-8 -*-
from flask.ext.wtf import Form
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class EditProfileForm(Form):
    name = StringField('真实姓名', validators=[Length(0, 64)])
    location = StringField('居住地', validators=[Length(0, 64)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('提交')


class UploadImagesForm(Form):
    upload = FileField('image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'png'], 'Images only!')
    ])
    submit = SubmitField("提交")


class ChatForm(Form):
    content = StringField('', validators=[DataRequired(), Length(1, 200, message="太长了。")])
    submit = SubmitField('发送')
