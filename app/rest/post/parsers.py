# -*- coding:utf-8 -*-
from flask_restful import reqparse

parser_basic = reqparse.RequestParser()
parser_basic.add_argument("token")
parser_basic.add_argument(
    "page", type=int, default=1, location=["json", "args", "headers"])

parser_post_get = parser_basic.copy()
parser_post_get.remove_argument("token")
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
