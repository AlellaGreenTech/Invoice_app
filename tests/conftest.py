"""Test configuration."""
import pytest
from app import create_app
from app.extensions import db
from app.models import User, Batch, Invoice, Category


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing."""
    user = User(
        google_id='test_google_id_123',
        email='test@example.com',
        name='Test User',
        picture_url='https://example.com/picture.jpg'
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def sample_batch(app, sample_user):
    """Create a sample batch for testing."""
    batch = Batch(
        user_id=sample_user.id,
        drive_url='https://drive.google.com/drive/folders/test123',
        status='completed',
        total_invoices=5,
        processed_invoices=5,
        failed_invoices=0,
        total_amount=5000.00,
        currency='USD'
    )
    db.session.add(batch)
    db.session.commit()
    return batch


@pytest.fixture
def sample_invoices(app, sample_batch):
    """Create sample invoices for testing."""
    invoices = [
        Invoice(
            batch_id=sample_batch.id,
            filename='invoice1.pdf',
            vendor_name='ACME Corp',
            invoice_number='INV-001',
            total_amount=1000.00,
            currency='USD',
            category='Office Supplies',
            category_confidence=0.95,
            status='categorized'
        ),
        Invoice(
            batch_id=sample_batch.id,
            filename='invoice2.pdf',
            vendor_name='Travel Co',
            invoice_number='INV-002',
            total_amount=2000.00,
            currency='USD',
            category='Travel',
            category_confidence=0.90,
            status='categorized'
        ),
        Invoice(
            batch_id=sample_batch.id,
            filename='invoice3.pdf',
            vendor_name='Software Inc',
            invoice_number='INV-003',
            total_amount=500.00,
            currency='USD',
            category='Software & Technology',
            category_confidence=0.85,
            status='categorized'
        )
    ]

    for invoice in invoices:
        db.session.add(invoice)

    db.session.commit()
    return invoices
