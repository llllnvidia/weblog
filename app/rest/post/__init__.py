# -*- coding:utf-8 -*-
from flask import current_app, abort
from flask_restful import Resource, marshal_with

from .fields import post_get_fields, tag_fields
from .parsers import parser_post_get
from ...models.account import User
from ...models.post import Post, Category, Tag


class PostApi(Resource):
    """Post Restful View"""

    @marshal_with(post_get_fields)
    def get(self, post_id=None):
        if post_id:
            post = Post.query.get_or_404(post_id)
            return post, 200

        # args parser
        args = parser_post_get.parse_args(strict=True)
        is_desc = args.get("desc", False)
        page_no = args.get("page")
        author_name = args.get("author", None)
        category_name = args.get("category", None)
        tags = args.get("tags", [])

        # posts filter by args
        post_selected = Post.query
        if is_desc:
            post_selected = post_selected.order_by(Post.timestamp.desc())
        else:
            post_selected = post_selected.order_by(Post.count.desc())
        if author_name:
            author = User.query.filter_by(username=author_name).first()
            post_selected = post_selected.filter_by(author=author)
        if category_name:
            category = Category.query.filter_by(name=category_name).first()
            if category:
                post_selected = category.posts_query(post_selected)
        if tags:
            for tag_name in tags:
                tag = Tag.query.filter_by(name=tag_name).first()
                if tag:
                    post_selected = tag.posts_query(post_selected)

        # paginate
        post_selected = post_selected.paginate(
            page=page_no,
            per_page=current_app.config.get("POSTS_PER_PAGE", 10),
            error_out=False)
        return {
            "page": page_no,
            "pagesize": post_selected.pages,
            "totalsize": post_selected.total,
            "post": post_selected.items
        }, 200

    def post(self, post_id=None):
        if post_id:
            abort(405)

        # todo:完善PostApi post method
        post_new = Post()

    def put(self, post_id=None):
        if not post_id:
            abort(400)

        # todo:完善PostApi put method
        post_edit = Post.query.get_or_404(post_id)

    def delete(self, post_id=None):
        if not post_id:
            abort(400)

        # todo:完善PostApi delete method
        post_delete = Post.query.get_or_404(post_id)


class TagApi(Resource):
    @marshal_with(tag_fields)
    def get(self):
        tags = Tag.query.all()
        return tags
