# -*- coding: utf-8 -*-
from flask import render_template, session, redirect, url_for, current_app, flash, \
                    request, abort, make_response
from .. import db
from ..models import User, Role, Permission, Post, Comment, Category
from ..email import send_email
from . import main
from .forms import TalkForm, EditProfileForm, EditProfileAdminForm, CommentForm, ArticleForm
from flask.ext.login import current_user, login_required
from ..decorators import admin_required,permission_required

@main.route('/',methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@main.route('/neighbourhood', methods=['GET', 'POST'])
def neighbourhood():
    Admin = User.query.filter_by(username='Admin').first()
    post = Admin.posts.order_by(Post.timestamp.desc()).first()
    page = request.args.get('page',1,type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query.filter(Post.author_id!=Admin.id)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page,per_page=current_app.config['CODEBLOG_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('neighbourhood.html',post=post,User=User,posts=posts,
                           show_followed=show_followed,
                           pagination=pagination)

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.neighbourhood')+'#neighbourhood'))
    resp.set_cookie('show_followed','',max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.neighbourhood')+'#neighbourhood'))
    resp.set_cookie('show_followed','1',max_age=30*24*60*60)
    return resp
    
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.filter_by(is_article=True).order_by(Post.timestamp.desc()).all()
    return render_template('user.html',user=user,posts=posts)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('需登录。')
        return redirect( url_for('.neighbourhood'))
    if current_user.is_following(user):
        flash('你已经关注了%s。'%username)
        return redirect( url_for('.user',username=username))
    current_user.follow(user)
    flash('你关注了%s。'%username)
    return redirect( url_for('.user',username=username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('需登录。')
        return redirect( url_for('.neighbourhood'))
    if current_user.is_following(user) :
        current_user.unfollow(user)
        flash('你取消了对%s的关注。'%username)
    else :
        flash('你没有关注过%s。'%username)
        return redirect( url_for('.user',username=username))
    return redirect( url_for('.user',username=username))

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('需登录。')
        return redirect( url_for('.neighbourhood'))
    page = request.args.get('page',1,type=int)
    pagination = user.followers.paginate(
        page,per_page=current_app.config['CODEBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user':item.follower,'timestamp':item.timestamp}
        for item in pagination.items]
    return render_template('followers.html',user=user,title="Followers of",
        endpoint='.followers',pagination=pagination,follows=follows)

@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('需登录。')
        return redirect(url_for('.neighbourhood'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['CODEBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)

@main.route('/edit-profile',methods=['GET','POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('你的资料已修改。')
        return redirect(url_for('.user',username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html',form=form)

@main.route('/edit-profile/<int:id>',methods=['GET','POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('资料已修改。')
        return redirect(url_for('.user',username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile_admin.html',form=form,user=user)

@main.route('/article/<int:id>', methods=['GET','POST'])
def article(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('你的评论已提交。')
        return redirect(url_for('.article', id=post.id,page=-1))
    page = request.args.get('page',1,type=int)
    if page == -1:
        page = (post.comments.count() - 1) / \
               current_app.config['CODEBLOG_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['CODEBLOG_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('article.html',posts=[post],form=form,
                           comments=comments, pagination=pagination,page=page)

@main.route('/new/article',methods=['GET','POST'])
@login_required
def new_Article():
    form = ArticleForm()
    if request.method == 'POST' :
        post = Post(body=form.body.data,title=form.title.data,
                    author=current_user._get_current_object(),
                    is_article = True,category=form.category.data)
        post.ping()
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.article',id=post.id))
    return render_template('edit_post.html',form=form,is_new='',article=True)

@main.route('/edit/article/<int:id>',methods=['GET','POST'])
@login_required
def edit_Article(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(0x0f):
        abort(403)
    if post.category :
        form = ArticleForm(category=post.category.id)
    else :
        form = ArticleForm()
    if request.method == 'POST' :
        post.title = form.title.data
        post.body = form.body.data
        post.category = Category.query.filter_by(id=form.category.data[0]).first()
        post.is_article = True
        post.ping()
        db.session.add(post)
        db.session.commit()
        flash('该文章已修改。')
        return redirect(url_for('.article',id=post.id))
    form.title.data = post.title
    form.body.data = post.body
    return render_template('edit_post.html',form=form,is_new=int(id),article=True,post=post)

@main.route('/delete-post/<int:id>',methods=['GET','POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)    
    if current_user != post.author and \
            not current_user.can(0x0f):
        abort(403)
    else:
        post.delete()
        flash('已删除！')
        return redirect(url_for('.neighbourhood'))

@main.route('/comment')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page',1,type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['CODEBLOG_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('comments.html', comments=comments,
                           pagination=pagination, page=page )
        
@main.route('/comment/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                            id=comment.post_id,page=request.args.get('page',1,type=int)))
                            
@main.route('/comment/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate',
                           id=comment.post_id,page=request.args.get('page',1,type=int)))
                           
@main.route('/users')
@login_required
@permission_required(0x0f)
def users():
    page = request.args.get('page',1,type=int)
    pagination = User.query.filter_by().paginate(
        page,per_page=current_app.config['CODEBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    users = [{'user':item.username,'name':item.name,
             'member_since':item.member_since,'last_seen':item.last_seen}
        for item in pagination.items]
    return render_template('users.html',title="所有用户",
        endpoint='.users',pagination=pagination,users=users)

@main.route('/categorys')
@login_required
@permission_required(0x0f)
def categorys():
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.filter_by().paginate(
        page, per_page=current_app.config['CODEBLOG_FOLLOWERS_PER_PAGE'],
        error_out=False)
    categorys = list()
    for item in pagination.items :
        arg = {'name': item.name}
        if item.parentcategory :
            arg.update({'parentcategory': Category.query.filter_by(id=item.parentid).first().name})
        else :
            arg.update({'parentcategory': 'None'})
        if item.soncategorys :
            arg.update({'soncategorys': ' '.join([category.name for category in item.soncategorys])})
        else :
            arg.update({'soncategorys': 'None'})

        arg.update({'count':item.posts.count()})

        categorys.append(arg)

    return render_template('categorys.html', title="所有栏目",
                           endpoint='.categorys', pagination=pagination, categorys=categorys)

@main.route('/new/talk',methods=['GET','POST'])
@login_required
def new_Talk():
    form = TalkForm()
    if form.validate_on_submit():
        talk = Post(body=form.body.data,
                    is_article=False,
                    author=current_user._get_current_object())
        db.session.add(talk)
        db.session.commit()
        return redirect(url_for('.neighbourhood',id=talk.id))
    return render_template('edit_post.html',form=form,article=False)

@main.route('/edit/talk/<int:id>',methods=['GET','POST'])
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def edit_Talk(id):
    talk = Post.query.get_or_404(id)
    form = TalkForm()
    if form.validate_on_submit():
        talk.body = form.body.data
        talk.ping()
        db.session.add(talk)
        db.session.commit()
        flash("已修改。")
        return redirect(url_for('main.neighbourhood'))
    form.body.data = talk.body
    return render_template('edit_post.html',form=form,is_new=int(id),article=False,post=talk)