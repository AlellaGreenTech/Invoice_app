"""Exports blueprint initialization."""
from flask import Blueprint

exports_bp = Blueprint('exports', __name__)

from app.exports import routes
