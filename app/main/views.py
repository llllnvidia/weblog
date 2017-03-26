# -*- coding: utf-8 -*-
from os import path

from flask import current_app, render_template, send_file, abort

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
    posts = Post.query.paginate(
        page=page_no,
        per_page=current_app.config.get("POSTS_PER_PAGE", 10),
        error_out=False)
    return render_template("index.html", posts=posts.items)


@main.route("/article/<int:post_id>")
def article(post_id=None):
    if post_id is None:
        abort(404)
    post = Post.query.getor404(post_id)
    return render_template("article.html", post)


@main.route("/images/<picture_name>")
def images(picture_name):
    """images provider"""
    import os.path
    path = current_app.config.get('IMG_PATH')
    try:
        return send_file(os.path.join(path, picture_name))
    except IOError:
        return send_file(os.path.join(path, '404.png'))
