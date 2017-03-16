# -*- coding:utf-8 -*-
from werkzeug.local import LocalProxy
from datetime import datetime, timedelta
from flask_restful import Resource
from flask import abort, request, _request_ctx_stack

from ...models.account import User
from .parsers import parser_auth


current_user = LocalProxy(lambda: _get_user())


def authenticate_required(func):
    def wrapper(*args, **kwargs):
        token_from_query_string = request.args.get("token", "")
        token_from_cookie = request.cookies.get("token", "")
        token_from_headers = request.headers.get("token", "")

        token = token_from_query_string or token_from_headers
        token = token or token_from_cookie

        user = User.confirm("login", token)
        is_valid = False
        if user:
            user.ping()
            is_valid = True
        if is_valid:
            response = func(*args, **kwargs)
            token = user.generate_token("login")
            expires_time = datetime.utcnow() + timedelta(0, 3600)
            expires = expires_time.strftime("%A %d-%b-%y %H:%M:%S UTC")
            headers = {"Set-Cookie":
                       f"token={token}; path=/; expires={expires}; HttpOnly"}
            response = response[0], response[1], headers
            return response
        abort(401)
    return wrapper


def _get_user():
    return getattr(_request_ctx_stack.top, 'user', None)


class AuthApi(Resource):
    def post(self):
        args = parser_auth.parse_args(strict=True)
        username = args.get("username")
        password = args.get("password")
        user = User.query.filter_by(username=username).first()
        is_valid = user.verify_password(password)
        if is_valid:
            user.ping()
            _request_ctx_stack.top.user = user
            token = user.generate_token("login")
            expires_time = datetime.utcnow() + timedelta(0, 3600)
            expires = expires_time.strftime("%A %d-%b-%y %H:%M:%S UTC")
            headers = {"Set-Cookie":
                       f"token={token}; path=/; expires={expires}; HttpOnly"}
            return {"token": token}, 200, headers
        else:
            return ({"message": "invalid username or password"},
                    401, {"Set-Cookie": "token=; path=/; Max-Age: 0;"})

    @authenticate_required
    def get(self):
        return {"message": "refresh token success"}, 200
