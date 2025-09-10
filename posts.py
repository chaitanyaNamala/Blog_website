from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from . import db
from .forms import PostForm
from .models import Post


posts_bp = Blueprint("posts", __name__, url_prefix="/posts")


def _can_modify_post(post: Post) -> bool:
    return current_user.is_authenticated and (post.user_id == current_user.id or current_user.is_admin)


@posts_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data.strip(), content=form.content.data, user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash("Post created.", "success")
        return redirect(url_for("index"))
    return render_template("post_form.html", form=form, heading="New Post")


@posts_bp.route("/<int:post_id>")
def detail(post_id: int):
    post = Post.query.get_or_404(post_id)
    return render_template("post_detail.html", post=post)


@posts_bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def edit(post_id: int):
    post = Post.query.get_or_404(post_id)
    if not _can_modify_post(post):
        abort(403)
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data.strip()
        post.content = form.content.data
        db.session.commit()
        flash("Post updated.", "success")
        return redirect(url_for("posts.detail", post_id=post.id))
    return render_template("post_form.html", form=form, heading="Edit Post")


@posts_bp.route("/<int:post_id>/delete", methods=["POST"]) 
@login_required
def delete(post_id: int):
    post = Post.query.get_or_404(post_id)
    if not _can_modify_post(post):
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "info")
    return redirect(url_for("index"))


