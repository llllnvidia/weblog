# -*- coding: utf-8 -*-
from flask import Blueprint

from app.models.account import Permission
from app.models.post import Post

main = Blueprint('main', __name__)

from . import views, errors


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission, Post=Post)
