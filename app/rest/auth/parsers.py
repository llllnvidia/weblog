# -*- coding:utf-8 -*-
from flask_restful import reqparse


from ...models.account import User


def username_checker(username):
    user = User.query.filter_by(username=username).first()
    if user:
        return username
    raise ValueError("valid ")


parser_auth = reqparse.RequestParser()
parser_auth.add_argument("username",
                         type=username_checker,
                         location=["header", "json"],
                         required=True,
                         help="{error_msg}username is required for authentication")
parser_auth.add_argument("password",
                         type=str,
                         location=["header", "json"],
                         required=True,
                         help="password is required for authentication")

parser_auth_refresh = reqparse.RequestParser()
parser_auth_refresh.add_argument("token",
                                 type=str,
                                 location=["header", "json", "args", "cookies"],
                                 required=True,
                                 help="token is required for refresh")