# -*- coding: utf-8 -*-
from flask import Blueprint

admin_manager = Blueprint('admin_manager', __name__)

from . import views
