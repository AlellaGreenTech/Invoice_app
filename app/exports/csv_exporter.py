"""CSV export functionality."""
import csv
import io
from datetime import datetime
from flask import current_app


class CSVExporter:
    """Exporter for generating CSV files from invoice data."""

    DEFAULT_COLUMNS = [
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

    def __init__(self):
        """Initialize CSV exporter."""
        pass

    def export_batch(self, batch, invoices, columns=None):
        """
        Export batch invoices to CSV.

        Args:
            batch: Batch model instance
            invoices: List of Invoice model instances
            columns: Optional list of column names to include

        Returns:
            str: CSV content as string
        """
        if columns is None:
            columns = self.DEFAULT_COLUMNS

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(columns)

        # Write invoice rows
        for invoice in invoices:
            row = self._invoice_to_row(invoice, columns)
            writer.writerow(row)

        # Add summary row
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Invoices', len(invoices)])
        writer.writerow(['Processed', batch.processed_invoices])
        writer.writerow(['Failed', batch.failed_invoices])
        writer.writerow(['Total Amount', f'{batch.currency or "USD"} {batch.total_amount or 0:.2f}'])

        if batch.date_range_start and batch.date_range_end:
            writer.writerow(['Date Range', f'{batch.date_range_start} to {batch.date_range_end}'])

        csv_content = output.getvalue()
        output.close()

        return csv_content

    def _invoice_to_row(self, invoice, columns):
        """
        Convert invoice to CSV row.

        Args:
            invoice: Invoice model instance
            columns: List of column names

        Returns:
            list: Row values
        """
        row = []

        for column in columns:
            if column == 'Invoice Number':
                row.append(invoice.invoice_number or '')
            elif column == 'Vendor Name':
                row.append(invoice.vendor_name or '')
            elif column == 'Invoice Date':
                row.append(invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else '')
            elif column == 'Amount':
                row.append(f'{invoice.total_amount:.2f}' if invoice.total_amount else '')
            elif column == 'Currency':
                row.append(invoice.currency or '')
            elif column == 'Category':
                row.append(invoice.category or '')
            elif column == 'Confidence':
                row.append(f'{invoice.category_confidence:.0%}' if invoice.category_confidence else '')
            elif column == 'Filename':
                row.append(invoice.filename or '')
            elif column == 'Status':
                row.append(invoice.status or '')
            else:
                row.append('')

        return row

    def generate_filename(self, batch):
        """
        Generate filename for CSV export.

        Args:
            batch: Batch model instance

        Returns:
            str: Filename
        """
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f'invoices_batch_{batch.id}_{timestamp}.csv'

    def export_to_file(self, batch, invoices, filepath, columns=None):
        """
        Export batch to CSV file.

        Args:
            batch: Batch model instance
            invoices: List of Invoice model instances
            filepath: Path to save CSV file
            columns: Optional list of column names

        Returns:
            str: Path to saved file
        """
        csv_content = self.export_batch(batch, invoices, columns)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            f.write(csv_content)

        current_app.logger.info(f'Exported batch {batch.id} to {filepath}')

        return filepath
