"""Gmail API handler for searching emails and downloading attachments."""
import base64
import io
from collections import defaultdict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app
from app.auth.google_auth import GoogleAuth


class GmailHandler:
    """Handler for Gmail API operations."""

    def __init__(self, user):
        """
        Initialize Gmail handler with user credentials.

        Args:
            user: User model instance with OAuth tokens
        """
        self.user = user
        self.credentials = GoogleAuth.get_credentials_from_user(user)
        self.service = build('gmail', 'v1', credentials=self.credentials)

    def search_emails(self, query, max_results=50, page_token=None):
        """
        Search emails using Gmail query syntax.

        Args:
            query: Gmail search query (e.g., "has:attachment from:vendor")
            max_results: Maximum number of results per page
            page_token: Token for pagination

        Returns:
            dict: {
                'messages': list of message summaries,
                'next_page_token': token for next page or None,
                'result_size_estimate': estimated total results
            }
        """
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                pageToken=page_token
            ).execute()

            messages = results.get('messages', [])
            next_page_token = results.get('nextPageToken')
            result_size_estimate = results.get('resultSizeEstimate', 0)

            current_app.logger.info(f'Gmail search found {len(messages)} messages for query: {query}')

            return {
                'messages': messages,
                'next_page_token': next_page_token,
                'result_size_estimate': result_size_estimate
            }

        except HttpError as error:
            current_app.logger.error(f'Gmail API error: {error}')
            if error.resp.status == 403:
                raise ValueError('Gmail access denied. Please re-authenticate with Gmail permissions.')
            else:
                raise ValueError(f'Failed to search Gmail: {error}')

    def get_message_with_attachments(self, message_id):
        """
        Get email details including attachment metadata.

        Args:
            message_id: Gmail message ID

        Returns:
            dict: Message details with attachments
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message.get('payload', {}).get('headers', [])
            header_dict = {h['name'].lower(): h['value'] for h in headers}

            # Extract attachments
            attachments = self._extract_attachments(message.get('payload', {}), message_id)

            return {
                'id': message_id,
                'thread_id': message.get('threadId'),
                'subject': header_dict.get('subject', '(No Subject)'),
                'from': header_dict.get('from', ''),
                'to': header_dict.get('to', ''),
                'date': header_dict.get('date', ''),
                'snippet': message.get('snippet', ''),
                'attachments': attachments
            }

        except HttpError as error:
            current_app.logger.error(f'Failed to get message {message_id}: {error}')
            raise ValueError(f'Failed to get email: {error}')

    def _extract_attachments(self, payload, message_id):
        """
        Recursively extract attachment metadata from message payload.

        Args:
            payload: Message payload
            message_id: Gmail message ID

        Returns:
            list: List of attachment dictionaries
        """
        attachments = []

        def process_part(part):
            filename = part.get('filename', '')
            mime_type = part.get('mimeType', '')
            body = part.get('body', {})
            attachment_id = body.get('attachmentId')
            size = body.get('size', 0)

            # If it has a filename and attachment ID, it's an attachment
            if filename and attachment_id:
                attachments.append({
                    'id': attachment_id,
                    'message_id': message_id,
                    'filename': filename,
                    'mime_type': mime_type,
                    'size': size
                })

            # Process nested parts
            for sub_part in part.get('parts', []):
                process_part(sub_part)

        process_part(payload)
        return attachments

    def download_attachment(self, message_id, attachment_id):
        """
        Download attachment content.

        Args:
            message_id: Gmail message ID
            attachment_id: Attachment ID

        Returns:
            bytes: Attachment content
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()

            data = attachment.get('data', '')
            # Gmail API returns base64url encoded data
            content = base64.urlsafe_b64decode(data)

            return content

        except HttpError as error:
            current_app.logger.error(f'Failed to download attachment: {error}')
            raise ValueError(f'Failed to download attachment: {error}')

    def aggregate_attachment_summary(self, messages_with_attachments):
        """
        Aggregate attachment statistics from a list of messages.

        Args:
            messages_with_attachments: List of message dicts with attachments

        Returns:
            dict: Summary statistics
        """
        summary = {
            'total_attachments': 0,
            'total_size': 0,
            'by_type': defaultdict(lambda: {'count': 0, 'size': 0}),
            'pdf_count': 0,
            'image_count': 0,
            'other_count': 0
        }

        for msg in messages_with_attachments:
            for att in msg.get('attachments', []):
                summary['total_attachments'] += 1
                summary['total_size'] += att.get('size', 0)

                mime_type = att.get('mime_type', 'unknown')
                summary['by_type'][mime_type]['count'] += 1
                summary['by_type'][mime_type]['size'] += att.get('size', 0)

                # Categorize
                if mime_type == 'application/pdf':
                    summary['pdf_count'] += 1
                elif mime_type.startswith('image/'):
                    summary['image_count'] += 1
                else:
                    summary['other_count'] += 1

        # Convert defaultdict to regular dict for JSON serialization
        summary['by_type'] = dict(summary['by_type'])

        return summary

    @staticmethod
    def build_date_query(date_from=None, date_to=None):
        """
        Build Gmail date filter query string.

        Args:
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)

        Returns:
            str: Gmail date query part
        """
        parts = []

        if date_from:
            parts.append(f'after:{date_from}')

        if date_to:
            parts.append(f'before:{date_to}')

        return ' '.join(parts)

    @staticmethod
    def format_size(size_bytes):
        """Format bytes as human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f'{size_bytes:.1f} {unit}'
            size_bytes /= 1024
        return f'{size_bytes:.1f} TB'
