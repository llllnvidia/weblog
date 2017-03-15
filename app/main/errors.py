# -*- coding: utf-8 -*-
from flask import render_template
from . import main


@main.app_errorhandler(403)
def forbidden(error):
    """error handler for 403"""
    return render_template(
        'errors/error.html', error_title="403", error_msg="FORBIDDEN!"), 403


@main.app_errorhandler(404)
def page_not_found(error):
    """error handler for 404"""
    return render_template(
        'errors/error.html', error_title="404", error_msg="YOU ARE LOST!"), 404


@main.app_errorhandler(500)
def internal_server_error(error):
    """error handler for 500"""
    return render_template(
        'errors/error.html', error_title="500",
        error_msg="INTERNAL ERROR!"), 500
