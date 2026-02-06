"""Google OAuth authentication helper."""
import os
import json
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from flask import current_app, session, url_for


class GoogleAuth:
    """Helper class for Google OAuth authentication."""

    def __init__(self):
        """Initialize Google OAuth flow."""
        self.client_config = {
            "web": {
                "client_id": current_app.config['GOOGLE_CLIENT_ID'],
                "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
            }
        }

        self.scopes = [
            'openid',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/gmail.readonly'
        ]

    def get_authorization_url(self):
        """
        Generate authorization URL for OAuth flow.

        Returns:
            tuple: (authorization_url, state)
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=current_app.config['GOOGLE_REDIRECT_URI']
        )

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent select_account'
        )

        return authorization_url, state

    def fetch_token(self, authorization_response, state):
        """
        Exchange authorization code for access token.

        Args:
            authorization_response: Full callback URL with code
            state: State parameter from session

        Returns:
            dict: Token information including access_token, refresh_token, etc.
        """
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            state=state,
            redirect_uri=current_app.config['GOOGLE_REDIRECT_URI']
        )

        flow.fetch_token(authorization_response=authorization_response)

        credentials = flow.credentials

        return {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_expiry': credentials.expiry,
            'scopes': credentials.scopes
        }

    def get_user_info(self, access_token):
        """
        Fetch user information from Google.

        Args:
            access_token: OAuth access token

        Returns:
            dict: User information (id, email, name, picture)
        """
        credentials = Credentials(token=access_token)
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()

        return {
            'google_id': user_info.get('id'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture_url': user_info.get('picture')
        }

    def refresh_access_token(self, refresh_token):
        """
        Refresh an expired access token.

        Args:
            refresh_token: OAuth refresh token

        Returns:
            dict: New token information
        """
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=self.client_config['web']['token_uri'],
            client_id=self.client_config['web']['client_id'],
            client_secret=self.client_config['web']['client_secret']
        )

        from google.auth.transport.requests import Request
        credentials.refresh(Request())

        return {
            'access_token': credentials.token,
            'token_expiry': credentials.expiry
        }

    @staticmethod
    def get_credentials_from_user(user):
        """
        Get Google credentials from user model.

        Args:
            user: User model instance

        Returns:
            Credentials: Google OAuth credentials
        """
        # Check if token is expired
        if user.token_expiry and user.token_expiry < datetime.utcnow():
            # Refresh token
            auth = GoogleAuth()
            new_token_info = auth.refresh_access_token(user.refresh_token)

            # Update user tokens
            user.access_token = new_token_info['access_token']
            user.token_expiry = new_token_info['token_expiry']

            from app.extensions import db
            db.session.commit()

        return Credentials(
            token=user.access_token,
            refresh_token=user.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=current_app.config['GOOGLE_CLIENT_ID'],
            client_secret=current_app.config['GOOGLE_CLIENT_SECRET']
        )
