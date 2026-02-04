"""Authentication routes."""
from flask import redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user, current_user
from app.auth import auth_bp
from app.auth.google_auth import GoogleAuth
from app.models import User
from app.extensions import db


@auth_bp.route('/login')
def login():
    """Initiate Google OAuth login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    # Check if OAuth is configured
    if not current_app.config.get('GOOGLE_CLIENT_ID'):
        flash('Google OAuth is not configured. Please set up credentials.', 'error')
        return redirect(url_for('main.index'))

    try:
        google_auth = GoogleAuth()
        authorization_url, state = google_auth.get_authorization_url()

        # Store state in session for verification
        session['oauth_state'] = state

        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error(f'OAuth login error: {str(e)}')
        flash('Failed to initiate login. Please try again.', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/callback')
def callback():
    """Handle Google OAuth callback."""
    # Verify state parameter
    state = session.get('oauth_state')
    if not state or state != request.args.get('state'):
        flash('Invalid state parameter. Please try again.', 'error')
        return redirect(url_for('main.index'))

    # Check for errors
    if 'error' in request.args:
        error = request.args.get('error')
        flash(f'Authentication failed: {error}', 'error')
        return redirect(url_for('main.index'))

    try:
        google_auth = GoogleAuth()

        # Exchange authorization code for tokens
        authorization_response = request.url
        token_info = google_auth.fetch_token(authorization_response, state)

        # Get user information
        user_info = google_auth.get_user_info(token_info['access_token'])

        # Find or create user
        user = User.query.filter_by(google_id=user_info['google_id']).first()

        if user:
            # Update existing user
            user.email = user_info['email']
            user.name = user_info['name']
            user.picture_url = user_info['picture_url']
            user.access_token = token_info['access_token']
            user.refresh_token = token_info.get('refresh_token') or user.refresh_token
            user.token_expiry = token_info['token_expiry']
            user.last_login = db.func.now()
        else:
            # Create new user
            user = User(
                google_id=user_info['google_id'],
                email=user_info['email'],
                name=user_info['name'],
                picture_url=user_info['picture_url'],
                access_token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                token_expiry=token_info['token_expiry']
            )
            db.session.add(user)

        db.session.commit()

        # Log in user
        login_user(user, remember=True)

        # Clear OAuth state from session
        session.pop('oauth_state', None)

        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('main.dashboard'))

    except Exception as e:
        current_app.logger.error(f'OAuth callback error: {str(e)}')
        flash('Authentication failed. Please try again.', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/logout')
def logout():
    """Logout user."""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))
