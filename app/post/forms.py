# -*- coding: utf-8 -*-
from flask_wtf import Form
from wtforms import StringField, TextAreaField, SelectField, SubmitField, ValidationError, BooleanField
from wtforms.validators import DataRequired, Length

from app.models.post import Category


def validate_tag(self, field):
    if field.data.find('，') != -1:
        raise ValidationError('请使用英文逗号‘,’来分隔标签。')


class ArticleForm(Form):
    title = StringField('标题', validators=[DataRequired()])
    summary = TextAreaField('摘要', validators=[DataRequired(), Length(1, 250, message="太长了。")])
    tags = StringField('标签', validators=[validate_tag])
    category = SelectField("栏目", coerce=int)
    is_draft = BooleanField("作为草稿")
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(ArticleForm, self).__init__(*args, **kwargs)
        self.category.choices = [(cg.id, cg.name) for cg in Category.query.all()]


class TalkForm(Form):
    body = TextAreaField("", validators=[DataRequired(), Length(1, 200, message="太长了。")])
    submit = SubmitField("说一说")


class CommentForm(Form):
    body = StringField('', validators=[DataRequired(), Length(1, 200, message="太长了。")])
    submit = SubmitField('提交')
