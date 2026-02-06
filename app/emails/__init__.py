"""Emails blueprint for Gmail integration."""
from flask import Blueprint

emails_bp = Blueprint('emails', __name__)

from app.emails import routes
