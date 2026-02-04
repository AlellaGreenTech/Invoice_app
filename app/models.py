"""Database models."""
from datetime import datetime
from flask_login import UserMixin
from app.extensions import db


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255))
    picture_url = db.Column(db.String(500))
    access_token = db.Column(db.Text)  # Should be encrypted in production
    refresh_token = db.Column(db.Text)  # Should be encrypted in production
    token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    batches = db.relationship('Batch', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='creator', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'


class Batch(db.Model):
    """Batch model for invoice processing jobs."""
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    drive_url = db.Column(db.String(1000), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    total_invoices = db.Column(db.Integer, default=0)
    processed_invoices = db.Column(db.Integer, default=0)
    failed_invoices = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(10))
    date_range_start = db.Column(db.Date)
    date_range_end = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)

    # Relationships
    invoices = db.relationship('Invoice', backref='batch', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Batch {self.id} - {self.status}>'

    @property
    def progress_percentage(self):
        """Calculate processing progress percentage."""
        if self.total_invoices == 0:
            return 0
        return int((self.processed_invoices / self.total_invoices) * 100)


class Invoice(db.Model):
    """Invoice model for individual invoice records."""
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=False)
    drive_file_id = db.Column(db.String(255))
    filename = db.Column(db.String(500), nullable=False)
    vendor_name = db.Column(db.String(255))
    invoice_number = db.Column(db.String(255))
    invoice_date = db.Column(db.Date)
    total_amount = db.Column(db.Numeric(15, 2))
    currency = db.Column(db.String(10))
    category = db.Column(db.String(255))
    category_confidence = db.Column(db.Float)
    raw_text = db.Column(db.Text)  # For debugging
    extraction_method = db.Column(db.String(50))  # pdfplumber or ocr
    status = db.Column(db.String(50), default='pending')  # pending, extracted, categorized, failed
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Invoice {self.filename}>'


class Category(db.Model):
    """Category model for invoice categorization."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    keywords = db.Column(db.JSON)  # Array of keywords for rule-based fallback
    is_default = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Category {self.name}>'
