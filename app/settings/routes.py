"""Settings routes."""
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.settings import settings_bp
from app.models import UserSettings
from app.extensions import db


SUPPORTED_CURRENCIES = ['EUR', 'USD', 'GBP']


@settings_bp.route('/')
@login_required
def index():
    """Display settings page."""
    # Get or create user settings
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id, base_currency='EUR')
        db.session.add(settings)
        db.session.commit()

    return render_template(
        'settings/index.html',
        settings=settings,
        currencies=SUPPORTED_CURRENCIES
    )


@settings_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Save settings."""
    base_currency = request.form.get('base_currency', 'EUR')

    if base_currency not in SUPPORTED_CURRENCIES:
        flash('Invalid currency selected', 'error')
        return redirect(url_for('settings.index'))

    # Get or create user settings
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)

    settings.base_currency = base_currency
    db.session.commit()

    flash('Settings saved successfully', 'success')
    return redirect(url_for('settings.index'))
