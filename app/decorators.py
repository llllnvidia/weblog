# -*- coding: utf-8 -*-
from functools import wraps

from flask import abort
from flask_login import current_user

from app.models.account import Permission


def permission_required(permission):
    """decorator for user permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """decorator for admin permission"""
    return permission_required(Permission.ADMINISTER)(f)
