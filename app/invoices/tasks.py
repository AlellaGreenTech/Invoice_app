"""Celery tasks for background invoice processing."""
import os
from datetime import datetime
from celery import shared_task
from flask import current_app
from app.extensions import db
from app.models import Batch, Invoice, UserSettings, TempUpload
from app.invoices.drive_handler import DriveHandler
from app.invoices.pdf_parser import PDFParser
from app.invoices.categorizer import InvoiceCategorizer
from app.utils.currency import CurrencyConverter


def _process_single_pdf(batch_id, filename, pdf_bytes, categorizer, pdf_parser, base_currency, drive_file_id=None):
    """
    Process a single PDF and create an Invoice record.

    Args:
        batch_id: ID of the batch
        filename: Name of the PDF file
        pdf_bytes: Raw PDF bytes (or BytesIO)
        categorizer: InvoiceCategorizer instance
        pdf_parser: PDFParser instance
        base_currency: User's base currency
        drive_file_id: Google Drive file ID (None for local uploads)

    Returns:
        dict with 'parsed_data' on success

    Raises:
        Exception on failure
    """
    parsed_data = pdf_parser.parse_invoice(pdf_bytes)

    if not parsed_data['success']:
        raise ValueError(parsed_data['error'])

    categorization = categorizer.categorize_invoice(parsed_data)

    converted_amount = None
    if parsed_data['total_amount'] and parsed_data['currency']:
        converted_amount = CurrencyConverter.convert(
            parsed_data['total_amount'],
            parsed_data['currency'],
            base_currency
        )

    invoice = Invoice(
        batch_id=batch_id,
        drive_file_id=drive_file_id,
        filename=filename,
        vendor_name=parsed_data['vendor_name'],
        invoice_number=parsed_data['invoice_number'],
        invoice_date=parsed_data['invoice_date'],
        total_amount=parsed_data['total_amount'],
        currency=parsed_data['currency'],
        currency_confidence=parsed_data.get('currency_confidence', 0.0),
        converted_amount=converted_amount,
        category=categorization['category'],
        category_confidence=categorization['confidence'],
        raw_text=parsed_data['raw_text'],
        extraction_method=parsed_data['extraction_method'],
        status='categorized'
    )

    db.session.add(invoice)
    return {'parsed_data': parsed_data}


def _finalize_batch(batch, batch_id, processed_count, failed_count, total_amount, date_range_start, date_range_end):
    """Finalize batch with results."""
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
            batch = Batch.query.get(batch_id)
            if not batch:
                raise ValueError(f'Batch {batch_id} not found')

            from app.models import User
            user = User.query.get(user_id)
            if not user:
                raise ValueError(f'User {user_id} not found')

            user_settings = UserSettings.query.filter_by(user_id=user_id).first()
            base_currency = user_settings.base_currency if user_settings else 'EUR'

            batch.status = 'processing'
            db.session.commit()

            drive_handler = DriveHandler(user)
            pdf_parser = PDFParser()
            categorizer = InvoiceCategorizer()

            app.logger.info(f'Processing batch {batch_id}: {batch.drive_url}')
            files = drive_handler.process_drive_url(batch.drive_url)

            batch.total_invoices = len(files)
            db.session.commit()

            processed_count = 0
            failed_count = 0
            total_amount = 0
            date_range_start = None
            date_range_end = None

            for i, file_info in enumerate(files):
                try:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': i + 1,
                            'total': len(files),
                            'status': f'Processing {file_info["name"]}'
                        }
                    )

                    file_content = drive_handler.download_file_to_memory(file_info['id'])

                    result = _process_single_pdf(
                        batch_id, file_info['name'], file_content,
                        categorizer, pdf_parser, base_currency,
                        drive_file_id=file_info['id']
                    )
                    parsed_data = result['parsed_data']

                    processed_count += 1

                    if parsed_data['total_amount']:
                        total_amount += float(parsed_data['total_amount'])

                    if parsed_data['invoice_date']:
                        if not date_range_start or parsed_data['invoice_date'] < date_range_start:
                            date_range_start = parsed_data['invoice_date']
                        if not date_range_end or parsed_data['invoice_date'] > date_range_end:
                            date_range_end = parsed_data['invoice_date']

                    batch.processed_invoices = processed_count
                    batch.failed_invoices = failed_count
                    db.session.commit()

                    app.logger.info(f'Successfully processed invoice: {file_info["name"]}')

                except Exception as e:
                    app.logger.error(f'Failed to process {file_info["name"]}: {str(e)}')

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

            _finalize_batch(batch, batch_id, processed_count, failed_count, total_amount, date_range_start, date_range_end)

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

            batch = Batch.query.get(batch_id)
            if batch:
                batch.status = 'failed'
                batch.error_message = str(e)
                db.session.commit()

            raise


@shared_task(bind=True)
def process_local_batch(self, batch_id, user_id):
    """
    Process a batch of locally uploaded PDFs stored in the temp_uploads table.

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
            batch = Batch.query.get(batch_id)
            if not batch:
                raise ValueError(f'Batch {batch_id} not found')

            user_settings = UserSettings.query.filter_by(user_id=user_id).first()
            base_currency = user_settings.base_currency if user_settings else 'EUR'

            batch.status = 'processing'
            db.session.commit()

            pdf_parser = PDFParser()
            categorizer = InvoiceCategorizer()

            # Read uploaded files from the database
            temp_files = TempUpload.query.filter_by(batch_id=batch_id).all()

            processed_count = 0
            failed_count = 0
            total_amount = 0
            date_range_start = None
            date_range_end = None
            total_files = len(temp_files)

            for i, temp in enumerate(temp_files):
                try:
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': i + 1,
                            'total': total_files,
                            'status': f'Processing {temp.filename}'
                        }
                    )

                    pdf_bytes = bytes(temp.file_data)

                    result = _process_single_pdf(
                        batch_id, temp.filename, pdf_bytes,
                        categorizer, pdf_parser, base_currency,
                        drive_file_id=None
                    )
                    parsed_data = result['parsed_data']

                    # Delete temp file after successful processing
                    db.session.delete(temp)

                    processed_count += 1

                    if parsed_data['total_amount']:
                        total_amount += float(parsed_data['total_amount'])

                    if parsed_data['invoice_date']:
                        if not date_range_start or parsed_data['invoice_date'] < date_range_start:
                            date_range_start = parsed_data['invoice_date']
                        if not date_range_end or parsed_data['invoice_date'] > date_range_end:
                            date_range_end = parsed_data['invoice_date']

                    batch.processed_invoices = processed_count
                    batch.failed_invoices = failed_count
                    db.session.commit()

                    app.logger.info(f'Successfully processed invoice: {temp.filename}')

                except Exception as e:
                    app.logger.error(f'Failed to process {temp.filename}: {str(e)}')

                    invoice = Invoice(
                        batch_id=batch_id,
                        drive_file_id=None,
                        filename=temp.filename,
                        status='failed',
                        error_message=str(e)
                    )
                    db.session.add(invoice)
                    # Still delete the temp file
                    db.session.delete(temp)
                    failed_count += 1

                    batch.failed_invoices = failed_count
                    db.session.commit()

            _finalize_batch(batch, batch_id, processed_count, failed_count, total_amount, date_range_start, date_range_end)

            app.logger.info(
                f'Local batch {batch_id} completed: {processed_count} processed, {failed_count} failed'
            )

            return {
                'status': 'completed',
                'processed': processed_count,
                'failed': failed_count,
                'total_amount': total_amount
            }

        except Exception as e:
            app.logger.error(f'Local batch processing failed: {str(e)}')

            # Clean up temp files on failure
            TempUpload.query.filter_by(batch_id=batch_id).delete()

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
