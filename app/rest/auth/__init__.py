# -*- coding:utf-8 -*-
from datetime import datetime, timedelta
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
            token = user.generate_token("login")
            expires_time = datetime.utcnow() + timedelta(0, 3600)
            expires = expires_time.strftime("%A %d-%b-%y %H:%M:%S UTC")
            headers = {"Set-Cookie":
                       f"token={token}; path=/; expires={expires}; HttpOnly"}
            return {"token": token}, 200, headers
        else:
            return ({"message": "invalid username or password"},
                    401, {"Set-Cookie": "token=; path=/; Max-Age: 0;"})

    def get(self):
        args = parser_auth_refresh.parse_args(strict=True)
        token = args.get("token")
        user = User.confirm("login", token)
        if user:
            user.ping()
            token = user.generate_token("login")
            expires_time = datetime.utcnow() + timedelta(0, 3600)
            expires = expires_time.strftime("%A %d-%b-%y %H:%M:%S UTC")
            headers = {"Set-Cookie":
                       f"token={token}; path=/; expires={expires}; HttpOnly"}
            return {"token": token}, 200, headers
        else:
            return ({"message": "invalid token"},
                    401, {"Set-Cookie": "token=; path=/; Max-Age: 0;"})
