from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

from . import db, login_manager


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    theme = db.Column(db.String(20), default="light")
    avatar_filename = db.Column(db.String(255), nullable=True)

    posts = db.relationship(
        "Post", backref="author", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def avatar_url(self) -> str:
        if self.avatar_filename:
            return "/static/uploads/avatars/" + self.avatar_filename
        return "/static/default-avatar.svg"

    # Password reset helpers
    def generate_reset_token(self, expires_in_seconds: int = 3600) -> str:
        secret_key = current_app.config.get("SECRET_KEY")
        salt = current_app.config.get("SECURITY_PASSWORD_SALT", "reset-salt")
        serializer = URLSafeTimedSerializer(secret_key=secret_key, salt=salt)
        return serializer.dumps({"user_id": self.id})

    @staticmethod
    def verify_reset_token(token: str, max_age_seconds: int = 3600):
        if not token:
            return None
        secret_key = current_app.config.get("SECRET_KEY")
        salt = current_app.config.get("SECURITY_PASSWORD_SALT", "reset-salt")
        serializer = URLSafeTimedSerializer(secret_key=secret_key, salt=salt)
        try:
            data = serializer.loads(token, max_age=max_age_seconds)
        except (BadSignature, SignatureExpired):
            return None
        user_id = data.get("user_id")
        if user_id is None:
            return None
        return User.query.get(user_id)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


