import os
from flask import Flask, send_from_directory, jsonify
from backend.config import Config
from backend.extensions import db, bcrypt


def create_app(config_object=Config):
    base = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    frontend_dir = os.path.join(base, "frontend")

    app = Flask(__name__, static_folder=None)
    app.config.from_object(config_object)

    db.init_app(app)
    bcrypt.init_app(app)

    from backend.routes.auth_routes import bp as auth_bp
    from backend.routes.admin_routes import bp as admin_bp
    from backend.routes.company_routes import bp as company_bp
    from backend.routes.student_routes import bp as student_bp
    from backend.routes.public_routes import bp as public_bp
    for bp in (auth_bp, admin_bp, company_bp, student_bp, public_bp):
        app.register_blueprint(bp)

    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>")
    def frontend_files(path):
        full = os.path.join(frontend_dir, path)
        if os.path.isfile(full):
            return send_from_directory(frontend_dir, path)
        # SPA fallback: unknown non-API paths return index.html
        return send_from_directory(frontend_dir, "index.html")

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "File too large (max 5MB)."}), 413

    return app


def seed_admin(app):
    from backend.models import User
    with app.app_context():
        db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin = User(
                email=app.config["ADMIN_EMAIL"],
                password=bcrypt.generate_password_hash(app.config["ADMIN_PASSWORD"]).decode("utf-8"),
                role="admin",
            )
            db.session.add(admin)
            db.session.commit()
            print(f"[seed] Admin created: {app.config['ADMIN_EMAIL']} / {app.config['ADMIN_PASSWORD']}")
