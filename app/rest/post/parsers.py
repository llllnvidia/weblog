# -*- coding:utf-8 -*-
from flask_restful import reqparse

from ...models.post import Category


def category_check(value):
    category = Category.query.filter_by(name=value).first()
    if category:
        return category
    raise ValueError


def tag_parser(value):
    tags = value.split(",")
    is_valid = False
    for tag in tags:
        if tag.startswith("'") and not tag.endswith("'"):
            break
        if tag.startswith("\"") and not tag.endswith("'"):
            break
        if not tag.startswith("'") and not tag.startswith("\""):
            break
        if len(tag[1:-1]) == 0:
            break
    else:
        is_valid = True
    if not is_valid:
        raise ValueError(r"""Tag sound format like 'A','B' or "A", "B" """)
    return [tag[1:-1] for tag in tags]


parser_post_get = reqparse.RequestParser()
parser_post_get.add_argument("desc", type=bool, location=["args"])
parser_post_get.add_argument("author", type=str, location=["args"])
parser_post_get.add_argument("category", type=str, location=["args"])
parser_post_get.add_argument(
    "tag", dest="tags", type=tag_parser, location=["args"], help="{error_msg}")

parser_post_post = reqparse.RequestParser()
parser_post_post.add_argument(
    "title",
    type=str,
    location=["json", "args"],
    required=True,
    help="title is required")
parser_post_post.add_argument(
    "summary",
    type=str,
    location=["json", "args"],
    required=True,
    help="summary is required")
parser_post_post.add_argument(
    "body",
    type=str,
    location=["json", "args"],
    required=True,
    help="body is required")
parser_post_post.add_argument(
    "category", type=category_check, location=["json", "args"])
parser_post_post.add_argument(
    "tag",
    dest="tags",
    type=tag_parser,
    location=["json", "args"],
    help="{error_msg}")

parser_post_put = reqparse.RequestParser()
parser_post_put.add_argument("title", type=str, location=["json", "args"])
parser_post_put.add_argument("summary", type=str, location=["json", "args"])
parser_post_put.add_argument("body", type=str, location=["json", "args"])
parser_post_put.add_argument(
    "category", type=category_check, location=["json", "args"])
parser_post_put.add_argument(
    "tag",
    dest="tags",
    type=tag_parser,
    location=["json", "args"],
    help="{error_msg}")
