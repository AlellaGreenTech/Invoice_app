"""Test models."""
import pytest
from datetime import datetime, date
from decimal import Decimal
from app.models import User, Batch, Invoice, Category
from app.extensions import db


class TestUserModel:
    """Test User model."""

    def test_create_user(self, app, sample_user):
        """Test creating a user."""
        assert sample_user.id is not None
        assert sample_user.email == 'test@example.com'
        assert sample_user.name == 'Test User'

    def test_user_repr(self, app, sample_user):
        """Test user string representation."""
        assert repr(sample_user) == '<User test@example.com>'

    def test_user_batches_relationship(self, app, sample_user, sample_batch):
        """Test user-batches relationship."""
        assert sample_batch in sample_user.batches.all()


class TestBatchModel:
    """Test Batch model."""

    def test_create_batch(self, app, sample_batch):
        """Test creating a batch."""
        assert sample_batch.id is not None
        assert sample_batch.status == 'completed'
        assert sample_batch.total_invoices == 5

    def test_batch_progress_percentage(self, app, sample_batch):
        """Test batch progress percentage calculation."""
        assert sample_batch.progress_percentage == 100

        # Test partial progress
        sample_batch.processed_invoices = 3
        assert sample_batch.progress_percentage == 60

        # Test zero total
        sample_batch.total_invoices = 0
        assert sample_batch.progress_percentage == 0

    def test_batch_repr(self, app, sample_batch):
        """Test batch string representation."""
        assert 'Batch' in repr(sample_batch)
        assert 'completed' in repr(sample_batch)

    def test_batch_invoices_relationship(self, app, sample_batch, sample_invoices):
        """Test batch-invoices relationship."""
        assert len(sample_batch.invoices.all()) == 3


class TestInvoiceModel:
    """Test Invoice model."""

    def test_create_invoice(self, app, sample_invoices):
        """Test creating an invoice."""
        invoice = sample_invoices[0]
        assert invoice.id is not None
        assert invoice.vendor_name == 'ACME Corp'
        assert invoice.total_amount == Decimal('1000.00')

    def test_invoice_repr(self, app, sample_invoices):
        """Test invoice string representation."""
        invoice = sample_invoices[0]
        assert 'Invoice' in repr(invoice)
        assert 'invoice1.pdf' in repr(invoice)

    def test_invoice_batch_relationship(self, app, sample_batch, sample_invoices):
        """Test invoice-batch relationship."""
        invoice = sample_invoices[0]
        assert invoice.batch == sample_batch


class TestCategoryModel:
    """Test Category model."""

    def test_create_category(self, app, sample_user):
        """Test creating a category."""
        category = Category(
            name='Test Category',
            description='A test category',
            keywords=['test', 'sample'],
            is_default=True,
            created_by=sample_user.id
        )
        db.session.add(category)
        db.session.commit()

        assert category.id is not None
        assert category.name == 'Test Category'
        assert category.keywords == ['test', 'sample']

    def test_category_repr(self, app):
        """Test category string representation."""
        category = Category(name='Test Category')
        assert 'Category' in repr(category)
        assert 'Test Category' in repr(category)


class TestModelCascadeDelete:
    """Test cascade delete behavior."""

    def test_delete_batch_deletes_invoices(self, app, sample_batch, sample_invoices):
        """Test that deleting a batch deletes its invoices."""
        batch_id = sample_batch.id
        invoice_ids = [inv.id for inv in sample_invoices]

        # Delete batch
        db.session.delete(sample_batch)
        db.session.commit()

        # Check batch is deleted
        assert Batch.query.get(batch_id) is None

        # Check invoices are deleted
        for invoice_id in invoice_ids:
            assert Invoice.query.get(invoice_id) is None

    def test_delete_user_deletes_batches(self, app, sample_user, sample_batch):
        """Test that deleting a user deletes their batches."""
        user_id = sample_user.id
        batch_id = sample_batch.id

        # Delete user
        db.session.delete(sample_user)
        db.session.commit()

        # Check user is deleted
        assert User.query.get(user_id) is None

        # Check batch is deleted
        assert Batch.query.get(batch_id) is None
