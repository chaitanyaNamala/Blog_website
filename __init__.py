from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from markupsafe import Markup, escape
import os

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app():
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static",
        template_folder="templates",
    )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-key"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", "sqlite:///" + os.path.join(app.instance_path, "app.db")
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads", "avatars"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,  # 2MB
        ALLOWED_IMAGE_EXTENSIONS={"png", "jpg", "jpeg", "gif"},
    )

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Jinja filters
    def nl2br(value: str) -> str:
        if value is None:
            return ""
        return Markup("<br>".join(escape(value).split("\n")))

    app.jinja_env.filters["nl2br"] = nl2br

    from .auth import auth_bp
    from .posts import posts_bp
    from .profile import profile_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(profile_bp)

    from .models import Post

    @app.route("/")
    def index():
        from flask import render_template

        posts = Post.query.order_by(Post.created_at.desc()).all()
        return render_template("index.html", posts=posts)

    return app


