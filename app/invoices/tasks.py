"""Celery tasks for background invoice processing."""
import os
from datetime import datetime
from celery import shared_task
from flask import current_app
from app.extensions import db
from app.models import Batch, Invoice
from app.invoices.drive_handler import DriveHandler
from app.invoices.pdf_parser import PDFParser
from app.invoices.categorizer import InvoiceCategorizer


@shared_task(bind=True)
def process_invoice_batch(self, batch_id, user_id):
    """
    Process a batch of invoices from Google Drive.

    Args:
        batch_id: ID of the batch to process
        user_id: ID of the user who owns the batch

    Returns:
        dict: Processing results
    """
    from app import create_app
    app = create_app()

    with app.app_context():
        try:
            # Get batch and user
            batch = Batch.query.get(batch_id)
            if not batch:
                raise ValueError(f'Batch {batch_id} not found')

            from app.models import User
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f'User {user_id} not found')

            # Update batch status
            batch.status = 'processing'
            db.session.commit()

            # Initialize handlers
            drive_handler = DriveHandler(user)
            pdf_parser = PDFParser()
            categorizer = InvoiceCategorizer()

            # Get list of files from Drive
            app.logger.info(f'Processing batch {batch_id}: {batch.drive_url}')
            files = drive_handler.process_drive_url(batch.drive_url)

            batch.total_invoices = len(files)
            db.session.commit()

            # Process each file
            processed_count = 0
            failed_count = 0
            total_amount = 0
            date_range_start = None
            date_range_end = None

            for i, file_info in enumerate(files):
                try:
                    # Update progress
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': i + 1,
                            'total': len(files),
                            'status': f'Processing {file_info["name"]}'
                        }
                    )

                    # Download file to memory
                    file_content = drive_handler.download_file_to_memory(file_info['id'])

                    # Parse PDF
                    parsed_data = pdf_parser.parse_invoice(file_content)

                    if not parsed_data['success']:
                        raise ValueError(parsed_data['error'])

                    # Categorize invoice
                    categorization = categorizer.categorize_invoice(parsed_data)

                    # Create invoice record
                    invoice = Invoice(
                        batch_id=batch_id,
                        drive_file_id=file_info['id'],
                        filename=file_info['name'],
                        vendor_name=parsed_data['vendor_name'],
                        invoice_number=parsed_data['invoice_number'],
                        invoice_date=parsed_data['invoice_date'],
                        total_amount=parsed_data['total_amount'],
                        currency=parsed_data['currency'],
                        category=categorization['category'],
                        category_confidence=categorization['confidence'],
                        raw_text=parsed_data['raw_text'],
                        extraction_method=parsed_data['extraction_method'],
                        status='categorized'
                    )

                    db.session.add(invoice)
                    processed_count += 1

                    # Update totals
                    if parsed_data['total_amount']:
                        total_amount += float(parsed_data['total_amount'])

                    # Update date range
                    if parsed_data['invoice_date']:
                        if not date_range_start or parsed_data['invoice_date'] < date_range_start:
                            date_range_start = parsed_data['invoice_date']
                        if not date_range_end or parsed_data['invoice_date'] > date_range_end:
                            date_range_end = parsed_data['invoice_date']

                    # Update batch progress
                    batch.processed_invoices = processed_count
                    batch.failed_invoices = failed_count
                    db.session.commit()

                    app.logger.info(f'Successfully processed invoice: {file_info["name"]}')

                except Exception as e:
                    app.logger.error(f'Failed to process {file_info["name"]}: {str(e)}')

                    # Create failed invoice record
                    invoice = Invoice(
                        batch_id=batch_id,
                        drive_file_id=file_info['id'],
                        filename=file_info['name'],
                        status='failed',
                        error_message=str(e)
                    )
                    db.session.add(invoice)
                    failed_count += 1

                    batch.failed_invoices = failed_count
                    db.session.commit()

            # Update batch with final results
            batch.status = 'completed'
            batch.processed_invoices = processed_count
            batch.failed_invoices = failed_count
            batch.total_amount = total_amount
            batch.date_range_start = date_range_start
            batch.date_range_end = date_range_end
            batch.completed_at = datetime.utcnow()

            # Determine currency (use most common)
            invoices = Invoice.query.filter_by(batch_id=batch_id).all()
            currencies = [inv.currency for inv in invoices if inv.currency]
            if currencies:
                batch.currency = max(set(currencies), key=currencies.count)

            db.session.commit()

            app.logger.info(
                f'Batch {batch_id} completed: {processed_count} processed, {failed_count} failed'
            )

            return {
                'status': 'completed',
                'processed': processed_count,
                'failed': failed_count,
                'total_amount': total_amount
            }

        except Exception as e:
            app.logger.error(f'Batch processing failed: {str(e)}')

            # Update batch status
            batch = Batch.query.get(batch_id)
            if batch:
                batch.status = 'failed'
                batch.error_message = str(e)
                db.session.commit()

            raise


@shared_task
def cleanup_old_batches(days=30):
    """
    Clean up old batches and their invoices.

    Args:
        days: Delete batches older than this many days

    Returns:
        int: Number of batches deleted
    """
    from app import create_app
    app = create_app()

    with app.app_context():
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        old_batches = Batch.query.filter(Batch.created_at < cutoff_date).all()

        count = len(old_batches)

        for batch in old_batches:
            db.session.delete(batch)

        db.session.commit()

        app.logger.info(f'Cleaned up {count} old batches')

        return count
