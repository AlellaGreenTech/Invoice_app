"""Updated invoice routes with background processing."""
from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.invoices import invoices_bp
from app.models import Batch, Invoice
from app.extensions import db
from app.invoices.tasks import process_invoice_batch


@invoices_bp.route('/upload')
@login_required
def upload():
    """Show upload form for Google Drive URL."""
    return render_template('invoices/upload.html')


@invoices_bp.route('/process', methods=['POST'])
@login_required
def process():
    """Process invoices from Google Drive URL."""
    drive_url = request.form.get('drive_url')

    if not drive_url:
        flash('Please provide a Google Drive URL', 'error')
        return redirect(url_for('invoices.upload'))

    try:
        # Create batch record
        batch = Batch(
            user_id=current_user.id,
            drive_url=drive_url,
            status='pending'
        )
        db.session.add(batch)
        db.session.commit()

        # Start background processing
        process_invoice_batch.delay(batch.id, current_user.id)

        flash('Processing started! You will be redirected to the progress page.', 'success')
        return redirect(url_for('invoices.processing', batch_id=batch.id))

    except Exception as e:
        import traceback
        from flask import current_app
        current_app.logger.error(f'Failed to start processing: {traceback.format_exc()}')
        flash(f'Failed to start processing: {str(e)}', 'error')
        return redirect(url_for('invoices.upload'))


@invoices_bp.route('/processing/<int:batch_id>')
@login_required
def processing(batch_id):
    """Show processing progress page."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))

    return render_template('invoices/processing.html', batch=batch)


@invoices_bp.route('/batch/<int:batch_id>')
@login_required
def batch_status(batch_id):
    """Get batch processing status (API endpoint)."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    return jsonify({
        'id': batch.id,
        'status': batch.status,
        'total_invoices': batch.total_invoices,
        'processed_invoices': batch.processed_invoices,
        'failed_invoices': batch.failed_invoices,
        'progress_percentage': batch.progress_percentage,
        'error_message': batch.error_message
    })


@invoices_bp.route('/batch/<int:batch_id>/summary')
@login_required
def batch_summary(batch_id):
    """Show batch summary dashboard."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))

    # Get category breakdown
    from sqlalchemy import func
    category_stats_rows = db.session.query(
        Invoice.category,
        func.count(Invoice.id).label('count'),
        func.sum(Invoice.total_amount).label('total')
    ).filter_by(batch_id=batch_id).group_by(Invoice.category).all()

    # Convert to JSON-serializable format
    category_stats = [
        {
            'category': row.category or 'Uncategorized',
            'count': row.count,
            'total': float(row.total) if row.total else 0
        }
        for row in category_stats_rows
    ]

    return render_template(
        'invoices/summary.html',
        batch=batch,
        category_stats=category_stats
    )


@invoices_bp.route('/batch/<int:batch_id>/details')
@login_required
def batch_details(batch_id):
    """Show detailed categorized invoice list."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))

    invoices = Invoice.query.filter_by(
        batch_id=batch_id
    ).order_by(
        Invoice.category,
        Invoice.vendor_name
    ).all()

    # Get unique categories for filter
    categories = db.session.query(Invoice.category).filter_by(
        batch_id=batch_id
    ).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]

    return render_template(
        'invoices/details.html',
        batch=batch,
        invoices=invoices,
        categories=categories
    )


@invoices_bp.route('/<int:invoice_id>/category', methods=['PUT'])
@login_required
def update_category(invoice_id):
    """Update invoice category."""
    invoice = Invoice.query.get_or_404(invoice_id)

    # Ensure user owns this invoice's batch
    if invoice.batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()
    new_category = data.get('category')

    if not new_category:
        return jsonify({'error': 'Category is required'}), 400

    invoice.category = new_category
    invoice.category_confidence = 1.0  # Manual categorization is 100% confident
    db.session.commit()

    return jsonify({'message': 'Category updated successfully'})


@invoices_bp.route('/batch/<int:batch_id>', methods=['DELETE'])
@login_required
def delete_batch(batch_id):
    """Delete a batch and all its invoices."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    db.session.delete(batch)
    db.session.commit()

    return jsonify({'message': 'Batch deleted successfully'})
