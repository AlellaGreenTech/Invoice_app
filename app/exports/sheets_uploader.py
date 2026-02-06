"""Google Sheets export functionality using googleapiclient."""
from googleapiclient.discovery import build
from flask import current_app
from app.auth.google_auth import GoogleAuth


class SheetsUploader:
    """Uploader for exporting invoice data to Google Sheets."""

    def __init__(self, user):
        """
        Initialize Sheets uploader with user credentials.

        Args:
            user: User model instance with OAuth tokens
        """
        self.user = user
        self.credentials = GoogleAuth.get_credentials_from_user(user)
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

    def export_batch(self, batch, invoices, spreadsheet_name=None):
        """
        Export batch to Google Sheets.

        Args:
            batch: Batch model instance
            invoices: List of Invoice model instances
            spreadsheet_name: Optional name for the spreadsheet

        Returns:
            dict: {
                'spreadsheet_id': str,
                'spreadsheet_url': str,
                'sheet_name': str
            }
        """
        try:
            # Generate spreadsheet name
            if not spreadsheet_name:
                from datetime import datetime
                timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
                spreadsheet_name = f'Invoices Batch #{batch.id} - {timestamp}'

            # Create new spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': spreadsheet_name
                },
                'sheets': [{
                    'properties': {
                        'title': f'Batch {batch.id}'
                    }
                }]
            }

            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()

            spreadsheet_id = spreadsheet['spreadsheetId']
            sheet_id = spreadsheet['sheets'][0]['properties']['sheetId']
            sheet_name = spreadsheet['sheets'][0]['properties']['title']

            # Prepare data
            headers = [
                'Invoice Number',
                'Vendor Name',
                'Invoice Date',
                'Amount',
                'Currency',
                'Category',
                'Confidence',
                'Filename',
                'Status'
            ]

            rows = [headers]

            # Add invoice data
            for invoice in invoices:
                row = [
                    invoice.invoice_number or '',
                    invoice.vendor_name or '',
                    invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                    float(invoice.total_amount) if invoice.total_amount else '',
                    invoice.currency or '',
                    invoice.category or '',
                    f'{invoice.category_confidence:.0%}' if invoice.category_confidence else '',
                    invoice.filename or '',
                    invoice.status or ''
                ]
                rows.append(row)

            # Add empty row
            rows.append([''] * len(headers))

            # Add summary
            rows.append(['Summary'])
            rows.append(['Total Invoices', len(invoices)])
            rows.append(['Processed', batch.processed_invoices])
            rows.append(['Failed', batch.failed_invoices])
            rows.append(['Total Amount', f'{batch.currency or "USD"} {batch.total_amount or 0:.2f}'])

            if batch.date_range_start and batch.date_range_end:
                rows.append(['Date Range', f'{batch.date_range_start} to {batch.date_range_end}'])

            # Update sheet with all data
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            # Format header row (bold and background color)
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True},
                            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            }]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

            spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'

            current_app.logger.info(
                f'Exported batch {batch.id} to Google Sheets: {spreadsheet_url}'
            )

            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'sheet_name': sheet_name
            }

        except Exception as e:
            current_app.logger.error(f'Failed to export to Google Sheets: {str(e)}')
            raise ValueError(f'Failed to export to Google Sheets: {str(e)}')

    def append_to_existing_sheet(self, spreadsheet_id, batch, invoices, sheet_name=None):
        """
        Append batch data to an existing spreadsheet.

        Args:
            spreadsheet_id: ID of existing spreadsheet
            batch: Batch model instance
            invoices: List of Invoice model instances
            sheet_name: Optional name for new sheet

        Returns:
            dict: Export result
        """
        try:
            # Create new sheet
            if not sheet_name:
                sheet_name = f'Batch {batch.id}'

            # Add new sheet
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': sheet_name
                    }
                }
            }]

            response = self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

            new_sheet_id = response['replies'][0]['addSheet']['properties']['sheetId']

            # Prepare data
            headers = [
                'Invoice Number',
                'Vendor Name',
                'Invoice Date',
                'Amount',
                'Currency',
                'Category',
                'Confidence',
                'Filename',
                'Status'
            ]

            rows = [headers]

            for invoice in invoices:
                row = [
                    invoice.invoice_number or '',
                    invoice.vendor_name or '',
                    invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '',
                    float(invoice.total_amount) if invoice.total_amount else '',
                    invoice.currency or '',
                    invoice.category or '',
                    f'{invoice.category_confidence:.0%}' if invoice.category_confidence else '',
                    invoice.filename or '',
                    invoice.status or ''
                ]
                rows.append(row)

            # Update sheet with data
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            # Format header
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': new_sheet_id,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {'bold': True},
                            'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8}
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            }]

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={'requests': requests}
            ).execute()

            spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'

            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'sheet_name': sheet_name
            }

        except Exception as e:
            current_app.logger.error(f'Failed to append to Google Sheets: {str(e)}')
            raise ValueError(f'Failed to append to Google Sheets: {str(e)}')

    def create_summary_sheet(self, batch, category_stats):
        """
        Create a summary-only sheet.

        Args:
            batch: Batch model instance
            category_stats: List of (category, count, total) tuples

        Returns:
            dict: Export result
        """
        try:
            from datetime import datetime
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
            spreadsheet_name = f'Invoice Summary - Batch #{batch.id} - {timestamp}'

            # Create spreadsheet
            spreadsheet_body = {
                'properties': {
                    'title': spreadsheet_name
                },
                'sheets': [{
                    'properties': {
                        'title': 'Summary'
                    }
                }]
            }

            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()

            spreadsheet_id = spreadsheet['spreadsheetId']
            sheet_name = 'Summary'

            # Prepare summary data
            rows = [
                ['Invoice Processing Summary'],
                [''],
                ['Batch ID', batch.id],
                ['Created', batch.created_at.strftime('%Y-%m-%d %H:%M')],
                ['Status', batch.status],
                [''],
                ['Statistics'],
                ['Total Invoices', batch.total_invoices],
                ['Processed', batch.processed_invoices],
                ['Failed', batch.failed_invoices],
                ['Total Amount', f'{batch.currency or "USD"} {batch.total_amount or 0:.2f}'],
                [''],
                ['Category Breakdown'],
                ['Category', 'Count', 'Total Amount']
            ]

            # Add category stats
            for category, count, total in category_stats:
                rows.append([
                    category or 'Uncategorized',
                    count,
                    float(total) if total else 0
                ])

            # Update sheet
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'{sheet_name}!A1',
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            spreadsheet_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}'

            return {
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': spreadsheet_url,
                'sheet_name': sheet_name
            }

        except Exception as e:
            current_app.logger.error(f'Failed to create summary sheet: {str(e)}')
            raise ValueError(f'Failed to create summary sheet: {str(e)}')
