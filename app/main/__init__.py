# -*- coding: utf-8 -*-
from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors


@main.app_context_processor
def inject_permissions():
    menu = ["main.index", "main.archives", "main.categories", "main.tags"]
    return dict(menu=menu)
