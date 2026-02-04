"""Test invoice categorization."""
import pytest
from app.invoices.categorizer import InvoiceCategorizer


class TestInvoiceCategorizer:
    """Test cases for invoice categorizer."""

    def setup_method(self):
        """Set up test fixtures."""
        self.categorizer = InvoiceCategorizer()

    def test_categorize_with_rules_office_supplies(self):
        """Test rule-based categorization for office supplies."""
        invoice_data = {
            'vendor_name': 'Staples',
            'total_amount': 150.00,
            'currency': 'USD',
            'raw_text': 'Office supplies including paper, pens, and folders'
        }

        result = self.categorizer.categorize_with_rules(invoice_data)

        assert result['category'] == 'Office Supplies'
        assert result['confidence'] > 0

    def test_categorize_with_rules_travel(self):
        """Test rule-based categorization for travel."""
        invoice_data = {
            'vendor_name': 'United Airlines',
            'total_amount': 450.00,
            'currency': 'USD',
            'raw_text': 'Flight ticket from New York to San Francisco'
        }

        result = self.categorizer.categorize_with_rules(invoice_data)

        assert result['category'] == 'Travel'
        assert result['confidence'] > 0

    def test_categorize_with_rules_software(self):
        """Test rule-based categorization for software."""
        invoice_data = {
            'vendor_name': 'Adobe',
            'total_amount': 52.99,
            'currency': 'USD',
            'raw_text': 'Adobe Creative Cloud subscription'
        }

        result = self.categorizer.categorize_with_rules(invoice_data)

        assert result['category'] == 'Software & Technology'
        assert result['confidence'] > 0

    def test_categorize_with_rules_no_match(self):
        """Test rule-based categorization with no clear match."""
        invoice_data = {
            'vendor_name': 'Unknown Vendor',
            'total_amount': 100.00,
            'currency': 'USD',
            'raw_text': 'Some random service'
        }

        result = self.categorizer.categorize_with_rules(invoice_data)

        assert result['category'] == 'Other'
        assert result['confidence'] < 0.5

    def test_get_default_categories(self):
        """Test getting default categories."""
        categories = InvoiceCategorizer.get_default_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert 'Office Supplies' in categories
        assert 'Travel' in categories
        assert 'Software & Technology' in categories
        assert 'Other' in categories

    def test_batch_categorize(self):
        """Test batch categorization."""
        invoices_data = [
            {
                'vendor_name': 'Staples',
                'total_amount': 150.00,
                'currency': 'USD',
                'raw_text': 'Office supplies'
            },
            {
                'vendor_name': 'United Airlines',
                'total_amount': 450.00,
                'currency': 'USD',
                'raw_text': 'Flight ticket'
            }
        ]

        results = self.categorizer.batch_categorize(invoices_data)

        assert len(results) == 2
        assert all('category' in result for result in results)
        assert all('confidence' in result for result in results)


class TestCategorizerKeywords:
    """Test keyword matching in categorizer."""

    def test_keyword_matching_case_insensitive(self):
        """Test that keyword matching is case insensitive."""
        categorizer = InvoiceCategorizer()

        invoice_data = {
            'vendor_name': 'STAPLES',
            'total_amount': 150.00,
            'currency': 'USD',
            'raw_text': 'OFFICE SUPPLIES'
        }

        result = categorizer.categorize_with_rules(invoice_data)

        assert result['category'] == 'Office Supplies'

    def test_multiple_keyword_matches(self):
        """Test that multiple keyword matches increase confidence."""
        categorizer = InvoiceCategorizer()

        invoice_data = {
            'vendor_name': 'Office Depot',
            'total_amount': 150.00,
            'currency': 'USD',
            'raw_text': 'Office supplies including paper and pens'
        }

        result = categorizer.categorize_with_rules(invoice_data)

        assert result['category'] == 'Office Supplies'
        # Multiple matches should give higher confidence
        assert result['confidence'] > 0.4
