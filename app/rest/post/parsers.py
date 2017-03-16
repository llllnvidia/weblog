# -*- coding:utf-8 -*-
from flask_restful import reqparse

from ...models.post import Category


def category_check(value):
    category = Category.query.filter_by(name=value).first()
    if category:
        return category
    raise ValueError


parser_post_get = reqparse.RequestParser()
parser_post_get.add_argument(
    "desc", type=bool, location=["json", "args", "headers"])
parser_post_get.add_argument(
    "author", type=str, location=["json", "args", "headers"])
parser_post_get.add_argument(
    "category", type=str, location=["json", "args", "headers"])
parser_post_get.add_argument(
    "tag",
    dest="tags",
    type=str,
    action="append",
    location=["json", "args", "headers"])

parser_post_post = reqparse.RequestParser()
parser_post_post.add_argument(
    "title",
    type=str,
    location=["json"],
    required=True,
    help="title is required")
parser_post_post.add_argument(
    "summary",
    type=str,
    location=["json"],
    required=True,
    help="summary is required")
parser_post_post.add_argument(
    "body",
    type=str,
    location=["json"],
    required=True,
    help="body is required")
parser_post_post.add_argument(
    "category", type=category_check, location=["json"])
parser_post_post.add_argument(
    "tag", dest="tags", type=str, action="append", location=["json"])

parser_post_put = reqparse.RequestParser()
parser_post_put.add_argument("title", type=str, location=["json"])
parser_post_put.add_argument("summary", type=str, location=["json"])
parser_post_put.add_argument("body", type=str, location=["json"])
parser_post_put.add_argument(
    "category", type=category_check, location=["json"])
parser_post_put.add_argument(
    "tag", dest="tags", type=str, action="append", location=["json"])
