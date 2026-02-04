"""Updated invoice routes with background processing."""
from flask import render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from app.invoices import invoices_bp
from app.models import Batch, Invoice, UserSettings
from app.extensions import db
from app.invoices.tasks import process_invoice_batch
from app.invoices.drive_handler import DriveHandler


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

    # Count invoices needing review
    needs_review_count = 0
    if batch.status == 'completed':
        invoices = Invoice.query.filter_by(batch_id=batch_id, status='categorized').all()
        needs_review_count = sum(1 for inv in invoices if inv.needs_review())

    return jsonify({
        'id': batch.id,
        'status': batch.status,
        'total_invoices': batch.total_invoices,
        'processed_invoices': batch.processed_invoices,
        'failed_invoices': batch.failed_invoices,
        'progress_percentage': batch.progress_percentage,
        'error_message': batch.error_message,
        'needs_review_count': needs_review_count
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

    # Get user's base currency
    user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    base_currency = user_settings.base_currency if user_settings else 'EUR'

    return render_template(
        'invoices/details.html',
        batch=batch,
        invoices=invoices,
        categories=categories,
        base_currency=base_currency
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


@invoices_bp.route('/<int:invoice_id>/update', methods=['PUT'])
@login_required
def update_invoice(invoice_id):
    """Update invoice details (amount, currency, category)."""
    invoice = Invoice.query.get_or_404(invoice_id)

    # Ensure user owns this invoice's batch
    if invoice.batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    # Update amount
    if 'total_amount' in data:
        if data['total_amount'] is not None:
            from decimal import Decimal
            invoice.total_amount = Decimal(str(data['total_amount']))
        else:
            invoice.total_amount = None

    # Update currency
    if 'currency' in data and data['currency']:
        invoice.currency = data['currency']
        invoice.currency_confidence = 1.0  # Manual entry is 100% confident

    # Update category
    if 'category' in data and data['category']:
        invoice.category = data['category']
        invoice.category_confidence = 1.0  # Manual entry is 100% confident

    # Recalculate converted amount if we have amount and currency
    if invoice.total_amount and invoice.currency:
        from app.utils.currency import CurrencyConverter
        user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        base_currency = user_settings.base_currency if user_settings else 'EUR'
        invoice.converted_amount = CurrencyConverter.convert(
            invoice.total_amount,
            invoice.currency,
            base_currency
        )

    # Mark as manually reviewed
    invoice.manually_reviewed = True
    db.session.commit()

    return jsonify({'message': 'Invoice updated successfully'})


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


@invoices_bp.route('/batch/<int:batch_id>/review')
@login_required
def batch_review(batch_id):
    """Review UI page for invoices needing review."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        flash('Unauthorized access', 'error')
        return redirect(url_for('main.dashboard'))

    # Get invoices needing review
    invoices = Invoice.query.filter_by(batch_id=batch_id, status='categorized').all()
    review_invoices = [inv for inv in invoices if inv.needs_review()]

    return render_template(
        'invoices/review.html',
        batch=batch,
        total_review_count=len(review_invoices)
    )


@invoices_bp.route('/batch/<int:batch_id>/review/next')
@login_required
def get_next_review(batch_id):
    """Get next invoice to review (API)."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Get invoices needing review
    invoices = Invoice.query.filter_by(batch_id=batch_id, status='categorized').all()
    review_invoices = [inv for inv in invoices if inv.needs_review()]

    if not review_invoices:
        return jsonify({
            'complete': True,
            'message': 'All invoices have been reviewed'
        })

    # Get the first one
    invoice = review_invoices[0]
    reviewed_count = len(invoices) - len(review_invoices)

    return jsonify({
        'complete': False,
        'invoice': {
            'id': invoice.id,
            'filename': invoice.filename,
            'vendor_name': invoice.vendor_name,
            'invoice_number': invoice.invoice_number,
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'total_amount': float(invoice.total_amount) if invoice.total_amount else None,
            'currency': invoice.currency,
            'currency_confidence': invoice.currency_confidence,
            'category': invoice.category,
            'category_confidence': invoice.category_confidence
        },
        'progress': {
            'reviewed': reviewed_count,
            'total': len(invoices),
            'remaining': len(review_invoices)
        }
    })


@invoices_bp.route('/<int:invoice_id>/review', methods=['PUT'])
@login_required
def submit_review(invoice_id):
    """Submit review for an invoice (API)."""
    invoice = Invoice.query.get_or_404(invoice_id)

    # Ensure user owns this invoice's batch
    if invoice.batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    data = request.get_json()

    # Update fields from review
    if 'currency' in data and data['currency']:
        invoice.currency = data['currency']
        invoice.currency_confidence = 1.0  # Manual review is 100% confident

        # Recalculate converted amount
        if invoice.total_amount:
            from app.utils.currency import CurrencyConverter
            user_settings = UserSettings.query.filter_by(user_id=current_user.id).first()
            base_currency = user_settings.base_currency if user_settings else 'EUR'
            invoice.converted_amount = CurrencyConverter.convert(
                invoice.total_amount,
                invoice.currency,
                base_currency
            )

    if 'category' in data and data['category']:
        invoice.category = data['category']
        invoice.category_confidence = 1.0  # Manual review is 100% confident

    if 'total_amount' in data and data['total_amount'] is not None:
        from decimal import Decimal
        invoice.total_amount = Decimal(str(data['total_amount']))

    # Mark as reviewed
    invoice.manually_reviewed = True
    db.session.commit()

    return jsonify({'message': 'Review submitted successfully'})


@invoices_bp.route('/<int:invoice_id>/skip', methods=['PUT'])
@login_required
def skip_review(invoice_id):
    """Skip review for an invoice, marking it as manually reviewed without changes."""
    invoice = Invoice.query.get_or_404(invoice_id)

    # Ensure user owns this invoice's batch
    if invoice.batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Mark as reviewed without changing anything
    invoice.manually_reviewed = True
    db.session.commit()

    return jsonify({'message': 'Invoice skipped'})


@invoices_bp.route('/<int:invoice_id>/pdf')
@login_required
def view_pdf(invoice_id):
    """Serve PDF file from Google Drive."""
    invoice = Invoice.query.get_or_404(invoice_id)

    # Ensure user owns this invoice's batch
    if invoice.batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if not invoice.drive_file_id:
        return jsonify({'error': 'No PDF file associated with this invoice'}), 404

    try:
        # Fetch PDF from Google Drive
        drive_handler = DriveHandler(current_user)
        pdf_content = drive_handler.download_file_to_memory(invoice.drive_file_id)

        # Return PDF as response
        return Response(
            pdf_content.read(),
            mimetype='application/pdf',
            headers={
                'Content-Disposition': f'inline; filename="{invoice.filename}"'
            }
        )
    except Exception as e:
        return jsonify({'error': f'Failed to fetch PDF: {str(e)}'}), 500
