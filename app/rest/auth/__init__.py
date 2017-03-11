# -*- coding:utf-8 -*-
from flask_restful import Resource

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
            return {"token": user.generate_token("login")}
        else:
            return {"msg": "invalid username or password"}, 401

    def __refresh(self):
        args = parser_auth_refresh.parse_args(strict=True)
        token = args.get("token")
        user = User.confirm("login", token)
        if user:
            user.ping()
            return {"token": user.generate_token("login")}
        else:
            return {"msg": "invalid token"}, 401

    get = __refresh
    put = __refresh

