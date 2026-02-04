"""Flask application factory."""
from flask import Flask
from flask_login import LoginManager
from app.config import config
from app.extensions import db, migrate, celery


def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

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

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(invoices_bp, url_prefix='/invoices')
    app.register_blueprint(exports_bp, url_prefix='/export')

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
