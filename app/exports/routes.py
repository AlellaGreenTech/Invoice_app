"""Export routes."""
import io
import zipfile
from flask import jsonify, send_file, request
from flask_login import login_required, current_user
from app.exports import exports_bp
from app.models import Batch, Invoice
from app.exports.csv_exporter import CSVExporter
from app.exports.sheets_uploader import SheetsUploader


@exports_bp.route('/csv/<int:batch_id>')
@login_required
def export_csv(batch_id):
    """Export batch to CSV."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Get invoices
    invoices = Invoice.query.filter_by(batch_id=batch_id).order_by(
        Invoice.category, Invoice.vendor_name
    ).all()

    try:
        # Generate CSV
        exporter = CSVExporter()
        csv_content = exporter.export_batch(batch, invoices)

        # Create file-like object
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.seek(0)

        # Generate filename
        filename = exporter.generate_filename(batch)

        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'Failed to export CSV: {str(e)}'}), 500


@exports_bp.route('/sheets/<int:batch_id>', methods=['POST'])
@login_required
def export_sheets(batch_id):
    """Export batch to Google Sheets."""
    from flask import current_app
    import traceback

    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    # Get invoices
    invoices = Invoice.query.filter_by(batch_id=batch_id).order_by(
        Invoice.category, Invoice.vendor_name
    ).all()

    try:
        # Get optional parameters (silent=True to handle empty body)
        data = request.get_json(silent=True) or {}
        spreadsheet_name = data.get('spreadsheet_name')
        existing_spreadsheet_id = data.get('existing_spreadsheet_id')

        current_app.logger.info(f'Starting Google Sheets export for batch {batch_id}')

        # Upload to Google Sheets
        uploader = SheetsUploader(current_user)

        if existing_spreadsheet_id:
            result = uploader.append_to_existing_sheet(
                existing_spreadsheet_id,
                batch,
                invoices
            )
        else:
            result = uploader.export_batch(batch, invoices, spreadsheet_name)

        current_app.logger.info(f'Successfully exported to Google Sheets: {result}')

        return jsonify({
            'message': 'Successfully exported to Google Sheets',
            'url': result['spreadsheet_url'],
            'spreadsheet_id': result['spreadsheet_id'],
            'sheet_name': result['sheet_name']
        })

    except Exception as e:
        current_app.logger.error(f'Google Sheets export error: {traceback.format_exc()}')
        return jsonify({'error': f'Failed to export to Google Sheets: {str(e)}'}), 500


@exports_bp.route('/sheets/<int:batch_id>/summary', methods=['POST'])
@login_required
def export_summary_sheets(batch_id):
    """Export batch summary to Google Sheets."""
    batch = Batch.query.get_or_404(batch_id)

    # Ensure user owns this batch
    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    try:
        # Get category stats
        from sqlalchemy import func
        from app.extensions import db

        category_stats = db.session.query(
            Invoice.category,
            func.count(Invoice.id).label('count'),
            func.sum(Invoice.total_amount).label('total')
        ).filter_by(batch_id=batch_id).group_by(Invoice.category).all()

        # Upload summary to Google Sheets
        uploader = SheetsUploader(current_user)
        result = uploader.create_summary_sheet(batch, category_stats)

        return jsonify({
            'message': 'Successfully exported summary to Google Sheets',
            'url': result['spreadsheet_url'],
            'spreadsheet_id': result['spreadsheet_id'],
            'sheet_name': result['sheet_name']
        })

    except Exception as e:
        return jsonify({'error': f'Failed to export summary: {str(e)}'}), 500


@exports_bp.route('/zip/<int:batch_id>')
@login_required
def export_zip(batch_id):
    """Export batch PDFs as ZIP organized by category (Drive batches only)."""
    batch = Batch.query.get_or_404(batch_id)

    if batch.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    if batch.upload_type == 'local':
        return jsonify({
            'error': 'ZIP export is not available for locally uploaded batches. '
                     'Original PDF files are not retained after processing.'
        }), 400

    invoices = Invoice.query.filter_by(batch_id=batch_id).filter(
        Invoice.drive_file_id.isnot(None)
    ).order_by(Invoice.category, Invoice.filename).all()

    if not invoices:
        return jsonify({'error': 'No invoices with PDF files found in this batch'}), 404

    try:
        from app.invoices.drive_handler import DriveHandler

        drive_handler = DriveHandler(current_user)
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for inv in invoices:
                category_folder = (inv.category or 'Uncategorized').replace('/', '-')
                try:
                    pdf_content = drive_handler.download_file_to_memory(inv.drive_file_id)
                    pdf_bytes = pdf_content.read()
                    zf.writestr(f'{category_folder}/{inv.filename}', pdf_bytes)
                except Exception:
                    continue

        zip_buffer.seek(0)
        filename = f'batch_{batch_id}_invoices.zip'

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({'error': f'Failed to create ZIP: {str(e)}'}), 500
