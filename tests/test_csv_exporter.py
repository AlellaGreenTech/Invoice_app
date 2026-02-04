"""Test CSV exporter."""
import pytest
from decimal import Decimal
from datetime import date
from app.exports.csv_exporter import CSVExporter


class TestCSVExporter:
    """Test CSV export functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = CSVExporter()

    def test_export_batch(self, app, sample_batch, sample_invoices):
        """Test exporting batch to CSV."""
        csv_content = self.exporter.export_batch(sample_batch, sample_invoices)

        assert csv_content is not None
        assert 'Invoice Number' in csv_content
        assert 'Vendor Name' in csv_content
        assert 'ACME Corp' in csv_content
        assert 'Travel Co' in csv_content

    def test_csv_has_summary(self, app, sample_batch, sample_invoices):
        """Test that CSV includes summary section."""
        csv_content = self.exporter.export_batch(sample_batch, sample_invoices)

        assert 'Summary' in csv_content
        assert 'Total Invoices' in csv_content
        assert str(len(sample_invoices)) in csv_content

    def test_generate_filename(self, app, sample_batch):
        """Test filename generation."""
        filename = self.exporter.generate_filename(sample_batch)

        assert filename.startswith('invoices_batch_')
        assert filename.endswith('.csv')
        assert str(sample_batch.id) in filename

    def test_invoice_to_row(self, app, sample_invoices):
        """Test converting invoice to CSV row."""
        invoice = sample_invoices[0]
        columns = self.exporter.DEFAULT_COLUMNS

        row = self.exporter._invoice_to_row(invoice, columns)

        assert len(row) == len(columns)
        assert 'ACME Corp' in row
        assert 'INV-001' in row

    def test_export_with_custom_columns(self, app, sample_batch, sample_invoices):
        """Test export with custom column selection."""
        custom_columns = ['Vendor Name', 'Amount', 'Category']

        csv_content = self.exporter.export_batch(
            sample_batch,
            sample_invoices,
            columns=custom_columns
        )

        lines = csv_content.split('\n')
        header = lines[0]

        assert 'Vendor Name' in header
        assert 'Amount' in header
        assert 'Category' in header
        assert 'Invoice Number' not in header


class TestCSVExporterEdgeCases:
    """Test edge cases for CSV exporter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = CSVExporter()

    def test_export_empty_batch(self, app, sample_batch):
        """Test exporting batch with no invoices."""
        csv_content = self.exporter.export_batch(sample_batch, [])

        assert csv_content is not None
        assert 'Invoice Number' in csv_content
        assert 'Summary' in csv_content

    def test_export_invoice_with_missing_fields(self, app, sample_batch):
        """Test exporting invoice with missing fields."""
        from app.models import Invoice

        invoice = Invoice(
            batch_id=sample_batch.id,
            filename='incomplete.pdf',
            status='failed'
        )

        csv_content = self.exporter.export_batch(sample_batch, [invoice])

        assert csv_content is not None
        assert 'incomplete.pdf' in csv_content

    def test_export_with_special_characters(self, app, sample_batch):
        """Test exporting invoice with special characters."""
        from app.models import Invoice

        invoice = Invoice(
            batch_id=sample_batch.id,
            filename='invoice.pdf',
            vendor_name='Company, Inc. "Special" & Co.',
            invoice_number='INV-001',
            total_amount=Decimal('1000.00'),
            currency='USD',
            category='Office Supplies',
            status='categorized'
        )

        csv_content = self.exporter.export_batch(sample_batch, [invoice])

        assert csv_content is not None
        assert 'Company, Inc.' in csv_content
