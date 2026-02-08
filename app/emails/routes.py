"""Email routes for Gmail search and attachment download."""
import io
import zipfile
from flask import render_template, request, jsonify, redirect, url_for, flash, Response, session, current_app
from flask_login import login_required, current_user
from googleapiclient.errors import HttpError
from app.emails import emails_bp
from app.emails.gmail_handler import GmailHandler


def _check_gmail_access():
    """Check if user has Gmail access. Returns redirect response if not, None if OK."""
    # If we already know gmail is authorized this session, skip check
    if session.get('gmail_authorized'):
        return None
    # Otherwise, we'll find out when the API call fails
    return None


@emails_bp.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Display search form and handle search submission."""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        date_from = request.form.get('date_from', '').strip()
        date_to = request.form.get('date_to', '').strip()

        if not query:
            flash('Please enter a search query', 'error')
            return redirect(url_for('emails.search'))

        # Build full query with date filters
        full_query = query
        date_query = GmailHandler.build_date_query(date_from, date_to)
        if date_query:
            full_query = f'{query} {date_query}'

        # Store search params in session
        session['email_search_query'] = full_query
        session['email_search_original_query'] = query
        session['email_search_date_from'] = date_from
        session['email_search_date_to'] = date_to

        return redirect(url_for('emails.results'))

    return render_template('emails/search.html')


@emails_bp.route('/results')
@login_required
def results():
    """Display search results with attachment summary."""
    query = session.get('email_search_query')

    if not query:
        flash('Please perform a search first', 'warning')
        return redirect(url_for('emails.search'))

    try:
        gmail = GmailHandler(current_user)
        page_token = request.args.get('page_token')

        # Search emails
        search_results = gmail.search_emails(query, max_results=25, page_token=page_token)
        messages = search_results['messages']

        # Get full details for each message
        messages_with_details = []
        for msg in messages:
            try:
                details = gmail.get_message_with_attachments(msg['id'])
                # Only include messages with attachments
                if details['attachments']:
                    messages_with_details.append(details)
            except Exception as e:
                current_app.logger.warning(f'Failed to get message {msg["id"]}: {e}')

        # Generate summary
        summary = gmail.aggregate_attachment_summary(messages_with_details)

        return render_template(
            'emails/results.html',
            messages=messages_with_details,
            summary=summary,
            query=session.get('email_search_original_query', query),
            date_from=session.get('email_search_date_from', ''),
            date_to=session.get('email_search_date_to', ''),
            next_page_token=search_results['next_page_token'],
            result_size_estimate=search_results['result_size_estimate'],
            format_size=GmailHandler.format_size
        )

    except HttpError as e:
        if e.resp.status == 403 and 'insufficientPermissions' in str(e):
            flash('Gmail access required. Please authorize Gmail to use this feature.', 'warning')
            return redirect(url_for('auth.authorize_gmail'))
        current_app.logger.error(f'Gmail API error: {e}')
        flash('Failed to search Gmail. Please try again.', 'error')
        return redirect(url_for('emails.search'))
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('emails.search'))
    except Exception as e:
        error_str = str(e)
        if 'insufficient' in error_str.lower() or 'scope' in error_str.lower():
            flash('Gmail access required. Please authorize Gmail to use this feature.', 'warning')
            return redirect(url_for('auth.authorize_gmail'))
        current_app.logger.error(f'Gmail search error: {e}')
        flash('Failed to search Gmail. Please try again.', 'error')
        return redirect(url_for('emails.search'))


@emails_bp.route('/load-more')
@login_required
def load_more():
    """Load more results via AJAX."""
    query = session.get('email_search_query')
    page_token = request.args.get('page_token')

    if not query or not page_token:
        return jsonify({'error': 'Invalid request'}), 400

    try:
        gmail = GmailHandler(current_user)

        # Search emails
        search_results = gmail.search_emails(query, max_results=25, page_token=page_token)
        messages = search_results['messages']

        # Get full details for each message
        messages_with_details = []
        for msg in messages:
            try:
                details = gmail.get_message_with_attachments(msg['id'])
                if details['attachments']:
                    # Build attachment URLs
                    for att in details['attachments']:
                        att['view_url'] = url_for('emails.view_attachment',
                            message_id=att['message_id'],
                            attachment_id=att['id'],
                            filename=att['filename'],
                            mime_type=att['mime_type'])
                        att['size_formatted'] = GmailHandler.format_size(att['size'])
                    messages_with_details.append(details)
            except Exception as e:
                current_app.logger.warning(f'Failed to get message {msg["id"]}: {e}')

        return jsonify({
            'messages': messages_with_details,
            'next_page_token': search_results['next_page_token']
        })

    except Exception as e:
        current_app.logger.error(f'Load more error: {e}')
        return jsonify({'error': 'Failed to load more results'}), 500


@emails_bp.route('/download', methods=['POST'])
@login_required
def download():
    """Download selected PDFs as a ZIP file."""
    try:
        data = request.get_json()
        attachments = data.get('attachments', [])

        if not attachments:
            return jsonify({'error': 'No attachments selected'}), 400

        # Limit total size to prevent memory issues (50MB)
        MAX_SIZE = 50 * 1024 * 1024
        total_size = sum(att.get('size', 0) for att in attachments)
        if total_size > MAX_SIZE:
            return jsonify({
                'error': f'Total size exceeds limit. Please select fewer files (max 50MB).'
            }), 400

        gmail = GmailHandler(current_user)

        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for att in attachments:
                try:
                    content = gmail.download_attachment(att['message_id'], att['id'])
                    filename = att.get('filename', 'attachment.pdf')
                    # Ensure unique filenames
                    zip_file.writestr(filename, content)
                except Exception as e:
                    current_app.logger.warning(f'Failed to download attachment: {e}')

        zip_buffer.seek(0)

        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename="email_attachments.zip"'
            }
        )

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f'Download error: {e}')
        return jsonify({'error': 'Failed to create ZIP file'}), 500


@emails_bp.route('/download-all-pdfs', methods=['POST'])
@login_required
def download_all_pdfs():
    """Download all PDFs from current search results as ZIP."""
    query = session.get('email_search_query')

    if not query:
        return jsonify({'error': 'No search results available'}), 400

    try:
        gmail = GmailHandler(current_user)

        # Search emails (get more results for bulk download)
        search_results = gmail.search_emails(query, max_results=100)
        messages = search_results['messages']

        # Collect all PDF attachments
        pdf_attachments = []
        total_size = 0
        MAX_SIZE = 50 * 1024 * 1024  # 50MB limit

        for msg in messages:
            try:
                details = gmail.get_message_with_attachments(msg['id'])
                for att in details['attachments']:
                    if att['mime_type'] == 'application/pdf':
                        if total_size + att['size'] <= MAX_SIZE:
                            pdf_attachments.append(att)
                            total_size += att['size']
            except Exception as e:
                continue

        if not pdf_attachments:
            return jsonify({'error': 'No PDF attachments found'}), 404

        # Create ZIP file
        zip_buffer = io.BytesIO()
        used_filenames = set()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for att in pdf_attachments:
                try:
                    content = gmail.download_attachment(att['message_id'], att['id'])
                    filename = att.get('filename', 'attachment.pdf')

                    # Ensure unique filename
                    base_filename = filename
                    counter = 1
                    while filename in used_filenames:
                        name_parts = base_filename.rsplit('.', 1)
                        if len(name_parts) == 2:
                            filename = f'{name_parts[0]}_{counter}.{name_parts[1]}'
                        else:
                            filename = f'{base_filename}_{counter}'
                        counter += 1

                    used_filenames.add(filename)
                    zip_file.writestr(filename, content)
                except Exception as e:
                    continue

        zip_buffer.seek(0)

        return Response(
            zip_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': 'attachment; filename="email_pdfs.zip"'
            }
        )

    except Exception as e:
        from flask import current_app
        current_app.logger.error(f'Bulk download error: {e}')
        return jsonify({'error': 'Failed to download PDFs'}), 500


@emails_bp.route('/attachment/<message_id>/<attachment_id>')
@login_required
def view_attachment(message_id, attachment_id):
    """View/download a single attachment."""
    try:
        gmail = GmailHandler(current_user)

        # Get the attachment content
        content = gmail.download_attachment(message_id, attachment_id)

        # Get filename from query param or use default
        filename = request.args.get('filename', 'attachment')
        mime_type = request.args.get('mime_type', 'application/octet-stream')

        # For PDFs, display inline; for others, download
        if mime_type == 'application/pdf':
            disposition = f'inline; filename="{filename}"'
        else:
            disposition = f'attachment; filename="{filename}"'

        return Response(
            content,
            mimetype=mime_type,
            headers={
                'Content-Disposition': disposition
            }
        )
    except Exception as e:
        current_app.logger.error(f'Failed to view attachment: {e}')
        flash('Failed to load attachment', 'error')
        return redirect(url_for('emails.results'))


@emails_bp.route('/process', methods=['POST'])
@login_required
def process_as_invoices():
    """Process downloaded PDFs through the invoice system."""
    # This is a placeholder for future integration
    # Would create a batch and process PDFs from Gmail
    flash('Invoice processing from Gmail is coming soon!', 'info')
    return redirect(url_for('emails.results'))
