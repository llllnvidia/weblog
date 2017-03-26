# -*- coding: utf-8 -*-
from flask import Blueprint
from ..rest.auth import current_user

main = Blueprint('main', __name__)

from . import views, errors


@main.app_context_processor
def inject_permissions():
    menu = ["main.index"]
    return dict(menu=menu, current_user=current_user)
