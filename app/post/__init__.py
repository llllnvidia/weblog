# -*- coding: utf-8 -*-
from flask import Blueprint


post = Blueprint('post', __name__)

from . import views, errors
