"""Main application routes."""
from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page."""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard showing recent batches."""
    from app.models import Batch
    batches = Batch.query.filter_by(user_id=current_user.id).order_by(Batch.created_at.desc()).limit(10).all()
    return render_template('dashboard.html', batches=batches)
