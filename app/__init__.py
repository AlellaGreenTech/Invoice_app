"""Flask application factory."""
import os
from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix
from app.config import config
from app.extensions import db, migrate, celery


def create_app(config_name=None):
    """Create and configure the Flask application."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development').strip()

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Trust reverse proxy headers (Render, Heroku, etc.)
    if config_name == 'production':
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize Celery
    celery.conf.update(app.config)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Register blueprints
    from app.auth import auth_bp
    from app.invoices import invoices_bp
    from app.exports import exports_bp
    from app.settings import settings_bp
    from app.emails import emails_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(exports_bp, url_prefix='/export')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(emails_bp, url_prefix='/emails')

    # Register main routes
    from app import routes
    app.register_blueprint(routes.main_bp)

    # Register error handlers
    from app import errors
    errors.register_error_handlers(app)

    # Register CLI commands
    from app import cli
    cli.register_commands(app)

    return app
