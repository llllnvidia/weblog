# -*- coding:utf-8 -*-
from flask import Blueprint

blueprint_api = Blueprint('api', __name__)

from .post import PostApi, TagApi
from .auth import AuthApi
from .. import api

api.init_app(blueprint_api)
api.add_resource(AuthApi, "/auth", endpoint="auth")
api.add_resource(PostApi, "/post", "/post/<int:post_id>", endpoint="post")
api.add_resource(TagApi, "/tag", endpoint="tag")
