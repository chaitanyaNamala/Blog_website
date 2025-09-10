import os
import secrets
from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from . import db
from .forms import ThemeForm
from .models import User, Post


profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


def _allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config.get("ALLOWED_IMAGE_EXTENSIONS", set())


@profile_bp.route("/<string:username>")
def view(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template("profile.html", profile_user=user, posts=posts)


@profile_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    form = ThemeForm(theme=current_user.theme)
    if form.validate_on_submit():
        current_user.theme = form.theme.data
        db.session.commit()
        flash("Theme updated.", "success")
        return redirect(url_for("profile.settings"))
    return render_template("settings.html", form=form)


@profile_bp.route("/avatar", methods=["POST"]) 
@login_required
def upload_avatar():
    file = request.files.get("avatar")
    if not file or file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("profile.settings"))
    if not _allowed_file(file.filename):
        flash("Invalid file type.", "error")
        return redirect(url_for("profile.settings"))
    random_hex = secrets.token_hex(8)
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    final_name = f"{current_user.id}_{random_hex}{ext.lower()}"
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], final_name)
    file.save(save_path)
    # Update user
    current_user.avatar_filename = final_name
    db.session.commit()
    flash("Avatar updated.", "success")
    return redirect(url_for("profile.settings"))


