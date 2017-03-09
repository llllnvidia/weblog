# -*- coding: utf-8 -*-
from os import path
from flask import current_app, send_file, render_template

from . import main
from ..models.post import Post


@main.before_app_first_request
def inject_context():
    menu = [{"endpoint": "main.index", "name": "Home"},
            {"endpoint": "main.archives", "name": "Archives"},
            {"endpoint": "main.categories", "name": "Categories"},
            {"endpoint": "main.tags", "name": "Tags"}]
    current_app.context_processor(lambda: {"menu": menu})


@main.route('/favicon.ico')
def favicon():
    """favicon icon"""
    return send_file(path.join(current_app.static_folder, "favicon.ico"))


@main.route('/', methods=['GET'])
def index():
    """main view"""
    return render_template("index.html")


@main.route("/archives")
def archives():
    return render_template("archives.html")


@main.route("/tags")
def tags():
    return render_template("tags.html")


@main.route("/categories")
def categories():
    return render_template("categories.html")


@main.route("/article/<int:post_id>")
def article(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template("article.html", post=post)


@main.route('/images/<picture_name>')
def images(picture_name):
    import os.path
    path = current_app.config.get('IMG_PATH')
    try:
        return send_file(os.path.join(path, picture_name))
    except IOError:
        return send_file(os.path.join(path, '404.png'))
