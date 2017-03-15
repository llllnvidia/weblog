# -*- coding:utf-8 -*-
from flask import url_for
from flask_restful import fields

tag_fields = {
    "id": fields.Integer(),
    "name": fields.String(),
    "count": fields.Integer(attribute=lambda t: t.posts_count())
}

author_fields = {
    "id": fields.Integer(),
    "username": fields.String(),
    "gravatar": fields.String()
}

post_fields = {
    "id": fields.Integer(),
    "link": fields.String(attribute=lambda p: url_for(
        "main.article", post_id=p.id,  _external=True)),
    "body": fields.String(),
    "timestamp": fields.DateTime(dt_format="iso8601"),
    "author": fields.Nested(author_fields),
    "title": fields.String(),
    "summary": fields.String(),
    "last_edit": fields.DateTime(dt_format="iso8601"),
    "count": fields.Integer(),
    "category_name": fields.String(
        attribute=lambda p: p.category.name if p.category else ""),
    "tags": fields.List(fields.Nested(tag_fields)),
}

post_get_fields = {
    "page": fields.Integer(),
    "pagesize": fields.Integer(),
    "totalsize": fields.Integer(),
    "post": fields.Nested(post_fields)
}
