"""Authentication routes."""
from flask import redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user, current_user
from app.auth import auth_bp
from app.auth.google_auth import GoogleAuth, LOGIN_SCOPES, GMAIL_SCOPES
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
        session['oauth_flow'] = 'login'

        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error(f'OAuth login error: {str(e)}')
        flash('Failed to initiate login. Please try again.', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/authorize-gmail')
def authorize_gmail():
    """Initiate incremental OAuth for Gmail access."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    try:
        google_auth = GoogleAuth()
        authorization_url, state = google_auth.get_gmail_authorization_url()

        session['oauth_state'] = state
        session['oauth_flow'] = 'gmail'

        return redirect(authorization_url)
    except Exception as e:
        current_app.logger.error(f'Gmail OAuth error: {str(e)}')
        flash('Failed to authorize Gmail access. Please try again.', 'error')
        return redirect(url_for('emails.search'))


@auth_bp.route('/callback')
def callback():
    """Handle Google OAuth callback for both login and incremental auth."""
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

    oauth_flow = session.get('oauth_flow', 'login')

    try:
        google_auth = GoogleAuth()

        # Determine which scopes to use for token exchange
        scopes = GMAIL_SCOPES if oauth_flow == 'gmail' else LOGIN_SCOPES

        # Fix request URL scheme for reverse proxy (Render, etc.)
        authorization_response = request.url
        if request.headers.get('X-Forwarded-Proto') == 'https' and authorization_response.startswith('http://'):
            authorization_response = 'https://' + authorization_response[7:]

        # Exchange authorization code for tokens
        token_info = google_auth.fetch_token(authorization_response, state, scopes=scopes)

        if oauth_flow == 'gmail':
            return _handle_gmail_callback(google_auth, token_info)
        else:
            return _handle_login_callback(google_auth, token_info)

    except Exception as e:
        current_app.logger.error(f'OAuth callback error: {type(e).__name__}: {str(e)}')
        current_app.logger.error(f'OAuth callback debug: request.url={request.url}, '
                                 f'authorization_response={authorization_response}, '
                                 f'flow={oauth_flow}')
        flash(f'Authentication failed: {type(e).__name__}: {str(e)}', 'error')
        return redirect(url_for('main.index'))


def _handle_login_callback(google_auth, token_info):
    """Handle the login OAuth callback."""
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
    session.pop('oauth_flow', None)

    flash(f'Welcome back, {user.name}!', 'success')
    return redirect(url_for('main.dashboard'))


def _handle_gmail_callback(google_auth, token_info):
    """Handle the incremental Gmail authorization callback."""
    # Update the current user's tokens (now includes gmail scope)
    current_user.access_token = token_info['access_token']
    if token_info.get('refresh_token'):
        current_user.refresh_token = token_info['refresh_token']
    current_user.token_expiry = token_info['token_expiry']

    db.session.commit()

    # Mark gmail as authorized in session
    session['gmail_authorized'] = True
    session.pop('oauth_state', None)
    session.pop('oauth_flow', None)

    flash('Gmail access authorized successfully!', 'success')
    return redirect(url_for('emails.search'))


@auth_bp.route('/debug-oauth')
def debug_oauth():
    """Debug endpoint showing OAuth configuration (no secrets)."""
    from urllib.parse import urlparse, parse_qs

    info = {
        'client_id_set': bool(current_app.config.get('GOOGLE_CLIENT_ID')),
        'client_id_preview': (current_app.config.get('GOOGLE_CLIENT_ID', '')[:20] + '...') if current_app.config.get('GOOGLE_CLIENT_ID') else 'NOT SET',
        'client_secret_set': bool(current_app.config.get('GOOGLE_CLIENT_SECRET')),
        'redirect_uri': current_app.config.get('GOOGLE_REDIRECT_URI', 'NOT SET'),
        'flask_env': current_app.config.get('ENV', 'unknown'),
        'debug': current_app.debug,
        'login_scopes': LOGIN_SCOPES,
    }

    try:
        google_auth = GoogleAuth()
        auth_url, _ = google_auth.get_authorization_url()
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        info['auth_url_params'] = {k: v[0] if len(v) == 1 else v for k, v in params.items()}
        # Redact state for security
        if 'state' in info['auth_url_params']:
            info['auth_url_params']['state'] = '(redacted)'
    except Exception as e:
        info['auth_url_error'] = str(e)

    from flask import jsonify
    return jsonify(info)


@auth_bp.route('/logout')
def logout():
    """Logout user and revoke Google token."""
    import requests
    from flask import make_response

    # Revoke Google token if user is logged in
    if current_user.is_authenticated and current_user.access_token:
        try:
            # Revoke the token on Google's side
            requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': current_user.access_token},
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
        except Exception as e:
            current_app.logger.warning(f'Failed to revoke token: {e}')

    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')

    # Create response and clear remember me cookie
    response = make_response(redirect(url_for('main.index')))
    response.delete_cookie('remember_token')
    response.delete_cookie('session')
    return response
