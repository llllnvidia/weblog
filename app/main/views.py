# -*- coding: utf-8 -*-
from os import path
from datetime import datetime

from flask import current_app, render_template, send_file, abort
from itertools import groupby

from . import main
from ..models.post import Post


@main.route("/favicon.ico")
def favicon():
    """favicon icon"""
    return send_file(path.join(current_app.static_folder, "favicon.ico"))


@main.route("/")
@main.route("/<int:page_no>")
def index(page_no=1):
    """main view"""
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page_no,
        per_page=current_app.config.get("POSTS_PER_PAGE", 10),
        error_out=False)
    return render_template(
        "index.html", posts=pagination.items, pagination=pagination)


@main.route("/archive")
@main.route("/archive/<int:page_no>")
def archive(page_no=1):
    """archive view"""
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page_no,
        per_page=current_app.config.get("POSTS_PER_PAGE", 10),
        error_out=False)

    def group(item):
        return item.timestamp.year, item.timestamp.month

    return render_template(
        "archive.html",
        archive=groupby(pagination.items, group),
        pagination=pagination)


@main.route("/article/<int:post_id>")
def article(post_id=None):
    if post_id is None:
        abort(404)
    post = Post.query.get_or_404(post_id)
    return render_template("article.html", post=post)


@main.route("/images/<picture_name>")
def images(picture_name):
    """images provider"""
    import os.path
    path = current_app.config.get('IMG_PATH')
    try:
        return send_file(os.path.join(path, picture_name))
    except IOError:
        return send_file(os.path.join(path, '404.png'))
