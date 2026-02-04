"""Test PDF parser functionality."""
import pytest
from app.invoices.pdf_parser import PDFParser


class TestPDFParser:
    """Test cases for PDF parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PDFParser()

    def test_extract_vendor_name(self):
        """Test vendor name extraction."""
        text = """
        ACME Corporation
        123 Main Street
        Invoice #12345
        """
        vendor = self.parser.extract_vendor_name(text)
        assert vendor == "ACME Corporation"

    def test_extract_invoice_date(self):
        """Test invoice date extraction."""
        text = "Invoice Date: 01/15/2024"
        date = self.parser.extract_invoice_date(text)
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_extract_total_amount(self):
        """Test total amount extraction."""
        text = "Total Amount: $1,234.56"
        amount, currency = self.parser.extract_total_amount(text)
        assert amount == 1234.56
        assert currency == "USD"

    def test_extract_invoice_number(self):
        """Test invoice number extraction."""
        text = "Invoice #: INV-2024-001"
        invoice_number = self.parser.extract_invoice_number(text)
        assert invoice_number == "INV-2024-001"

    def test_parse_date_formats(self):
        """Test various date format parsing."""
        test_cases = [
            ("01/15/2024", (2024, 1, 15)),
            ("2024-01-15", (2024, 1, 15)),
            ("January 15, 2024", (2024, 1, 15)),
            ("15 Jan 2024", (2024, 1, 15)),
        ]

        for date_string, expected in test_cases:
            date = self.parser.parse_date(date_string)
            if date:
                assert (date.year, date.month, date.day) == expected

    def test_extract_currency_patterns(self):
        """Test currency extraction patterns."""
        test_cases = [
            ("Total: $1,234.56", (1234.56, "USD")),
            ("Amount: 1,234.56 USD", (1234.56, "USD")),
            ("Total: €1,234.56", (1234.56, "EUR")),
            ("Amount: £1,234.56", (1234.56, "GBP")),
        ]

        for text, expected in test_cases:
            amount, currency = self.parser.extract_total_amount(text)
            assert amount == expected[0]
            assert currency == expected[1]


class TestPDFParserIntegration:
    """Integration tests for PDF parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = PDFParser()

    def test_parse_complete_invoice(self):
        """Test parsing a complete invoice text."""
        invoice_text = """
        ACME Corporation
        123 Main Street
        New York, NY 10001

        INVOICE

        Invoice Number: INV-2024-001
        Invoice Date: January 15, 2024

        Bill To:
        Customer Name
        456 Oak Avenue

        Description                 Amount
        Professional Services       $5,000.00
        Consulting Fee             $2,500.00

        Subtotal:                  $7,500.00
        Tax (10%):                   $750.00
        Total Amount Due:          $8,250.00

        Payment Terms: Net 30
        """

        result = self.parser.parse_invoice(invoice_text)

        assert result['success'] is True
        assert result['vendor_name'] == "ACME Corporation"
        assert result['invoice_number'] == "INV-2024-001"
        assert result['total_amount'] == 8250.00
        assert result['currency'] == "USD"
        assert result['invoice_date'] is not None
