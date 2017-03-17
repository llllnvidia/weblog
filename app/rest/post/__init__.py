# -*- coding:utf-8 -*-
from flask import current_app, abort, url_for
from flask_restful import Resource, marshal_with

from .fields import post_get_fields, tag_fields
from .parsers import parser_post_get, parser_post_post, parser_post_put
from ..auth import authenticate_required, current_user
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
        is_desc = args.get("desc") or False
        page_no = args.get("page")
        author_name = args.get("author")
        category_name = args.get("category")
        tags = args.get("tags") or []

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

    @authenticate_required
    def post(self, post_id=None):
        if post_id:
            abort(405)

        # parse_args
        args = parser_post_post.parse_args()
        title = args.get("title")
        summary = args.get("summary")
        body = args.get("body")
        category = args.get("category")
        tags = args.get("tags") or []

        # create new post
        post_new = Post(
            title=title, summary=summary, body=body, author=current_user)
        if category:
            post_new.category = category
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag is None:
                tag = Tag(name=tag_name)
                tag.save()
            post_new.tags.append(tag)
        post_new.save()
        return {"next": url_for("api.post", post_id=post_new.id)}, 201

    @authenticate_required
    def put(self, post_id=None):
        if not post_id:
            abort(400)

        post_edit = Post.query.get_or_404(post_id)
        if post_edit.author != current_user:
            return {"message": "forbidden"}, 403

        # parse_args
        args = parser_post_put.parse_args()
        title = args.get("title")
        summary = args.get("summary")
        body = args.get("body")
        category = args.get("category")
        tags = args.get("tags", [])

        # edit
        if title:
            post_edit.title = title
        if summary:
            post_edit.summary = summary
        if body:
            post_edit.body = body
        if category:
            post_edit.category = category
        if tags:
            post_edit.tags = []
        for tag_name in tags:
            tag = Tag.query.filter_by(name=tag_name).first()
            if tag is None:
                tag = Tag(name=tag_name)
                tag.save()
            post_edit.tags.append(tag)
        post_edit.save()
        return {"next": url_for("api.post", post_id=post_edit.id)}, 200

    @authenticate_required
    def delete(self, post_id=None):
        if not post_id:
            abort(400)

        post_delete = Post.query.get_or_404(post_id)
        if post_delete.author == current_user:
            post_delete.delete()
            return {"message": "delelet success"}, 204
        else:
            return {"message": "forbidden"}, 403


class TagApi(Resource):
    @marshal_with(tag_fields)
    def get(self):
        tags = Tag.query.all()
        return tags
