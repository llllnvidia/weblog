# -*- coding:utf-8 -*-
from flask import make_response
from flask_restful import Resource
from flask_login import login_required, current_user

from ... import login_manager
from ...models.account import User
from .parsers import parser_auth, parser_auth_refresh


class AuthApi(Resource):
    def post(self):
        args = parser_auth.parse_args(strict=True)
        username = args.get("username")
        password = args.get("password")
        user = User.query.filter_by(username=username).first()
        is_valid = user.verify_password(password)
        if is_valid:
            user.ping()
            resp = make_response()
            resp.headers['Authorization'] = user.generate_token("login")
            return resp
        else:
            return {"msg": "invalid username or password"}, 401

    @login_required
    def put(self):
        if current_user:
            current_user.ping()
            resp = make_response()
            resp.headers['Authorization'] = current_user.generate_token("login")
            return resp
        else:
            return {"msg": "invalid token"}, 401


@login_manager.user_loader
def user_loader(user_id):
    user = User.query.get(user_id)
    return user


@login_manager.header_loader
def header_loader(header_val):
    user = User.confirm("login", header_val)
    return user