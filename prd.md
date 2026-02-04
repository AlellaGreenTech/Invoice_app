# Invoice Processing Web Application - Implementation Plan

## Overview
Build a web application for CFOs to process invoices from Google Drive, automatically categorize them using AI, and export organized summaries to CSV or Google Sheets.

## Requirements Summary
- **Input**: Google Drive URL containing PDF invoices
- **Processing**: Extract invoice data (vendor, date, amount, currency) from PDFs
- **Categorization**: AI-powered automatic categorization using Claude API
- **Output**: Summary dashboard + detailed categorized list + CSV/Google Sheets export
- **Scale**: 50-200 invoices per batch
- **Deployment**: Local development with Docker, cloud deployment later

## Technology Stack

### Backend
- **Flask 3.x** - Lightweight web framework
- **PostgreSQL** - Database for invoices and batches
- **Celery + Redis** - Background job processing for batch operations
- **pdfplumber** - PDF text extraction
- **pytesseract** - OCR fallback for scanned PDFs
- **Claude API** - AI-powered invoice categorization

### Google Integration
- **google-auth + google-auth-oauthlib** - OAuth2 authentication
- **google-api-python-client** - Drive API access
- **gspread** - Google Sheets export

### Frontend
- **Jinja2 templates** - Server-side rendering
- **Bootstrap 5** - Responsive UI
- **HTMX** - Dynamic updates without heavy JavaScript
- **Chart.js** - Summary visualizations

### Local Development
- **Docker Compose** - Containerized services (Flask, PostgreSQL, Redis, Celery)

## Project Structure

```
invoice_app/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Configuration classes
│   ├── models.py                   # Database models (User, Batch, Invoice, Category)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py              # OAuth routes
│   │   └── google_auth.py         # Google OAuth helper
│   ├── invoices/
│   │   ├── __init__.py
│   │   ├── routes.py              # Invoice processing routes
│   │   ├── pdf_parser.py          # PDF extraction logic
│   │   ├── categorizer.py         # AI categorization with Claude
│   │   ├── drive_handler.py       # Google Drive operations
│   │   └── tasks.py               # Celery background tasks
│   ├── exports/
│   │   ├── __init__.py
│   │   ├── routes.py              # Export endpoints
│   │   ├── csv_exporter.py        # CSV generation
│   │   └── sheets_uploader.py     # Google Sheets integration
│   ├── static/
│   │   ├── css/custom.css
│   │   └── js/app.js
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html             # Landing page
│   │   ├── auth/login.html
│   │   ├── invoices/
│   │   │   ├── upload.html        # Drive URL input
│   │   │   ├── processing.html    # Progress view
│   │   │   ├── summary.html       # Summary dashboard
│   │   │   └── details.html       # Categorized list
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   └── utils/
│       ├── __init__.py
│       └── validators.py          # Input validation
├── migrations/                     # Database migrations
├── tests/
│   ├── __init__.py
│   ├── test_pdf_parser.py
│   ├── test_categorizer.py
│   └── fixtures/sample_invoices/
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── run.py                         # Application entry point
├── celery_worker.py              # Celery worker entry point
└── docker-compose.yml            # Local development setup
```

## Database Schema

### Users Table
- `id` (primary key)
- `google_id` (unique)
- `email` (unique)
- `name`
- `picture_url`
- `access_token` (encrypted)
- `refresh_token` (encrypted)
- `token_expiry`
- `created_at`, `last_login`

### Batches Table
- `id` (primary key)
- `user_id` (foreign key)
- `drive_url`
- `status` (pending, processing, completed, failed)
- `total_invoices`, `processed_invoices`, `failed_invoices`
- `total_amount`, `currency`
- `date_range_start`, `date_range_end`
- `created_at`, `completed_at`
- `error_message`

### Invoices Table
- `id` (primary key)
- `batch_id` (foreign key)
- `drive_file_id`, `filename`
- `vendor_name`, `invoice_number`, `invoice_date`
- `total_amount`, `currency`
- `category`, `category_confidence`
- `raw_text` (for debugging)
- `extraction_method` (pdfplumber or ocr)
- `status` (pending, extracted, failed)
- `error_message`
- `created_at`, `updated_at`

### Categories Table
- `id` (primary key)
- `name` (unique)
- `description`
- `keywords` (array for rule-based fallback)
- `is_default`
- `created_by` (foreign key to users)
- `created_at`

## Implementation Phases

### Phase 1: Foundation & Setup
**Goal**: Basic Flask app with Docker environment

**Tasks**:
1. Create Flask application structure with factory pattern
2. Set up Docker Compose (Flask, PostgreSQL, Redis)
3. Configure SQLAlchemy models (User, Batch, Invoice, Category)
4. Implement Google OAuth2 authentication flow
5. Create basic templates (base, login, dashboard)
6. Set up database migrations with Flask-Migrate

**Deliverable**: Users can log in with Google and see a dashboard

**Critical Files**:
- `docker-compose.yml`
- `app/__init__.py`
- `app/models.py`
- `app/config.py`
- `app/auth/routes.py`
- `app/auth/google_auth.py`

### Phase 2: Google Drive Integration
**Goal**: Fetch PDFs from Google Drive

**Tasks**:
1. Implement Drive API integration with proper scopes
2. Build Drive URL parser (handle folder/file URLs)
3. Create file listing and download functionality
4. Add validation for PDF file types
5. Implement error handling for access permissions
6. Create upload form and processing initiation

**Deliverable**: System can list and download PDFs from a shared Drive folder

**Critical Files**:
- `app/invoices/drive_handler.py`
- `app/invoices/routes.py`
- `app/templates/invoices/upload.html`

### Phase 3: PDF Processing & Data Extraction
**Goal**: Extract invoice data from PDFs

**Tasks**:
1. Implement pdfplumber-based text extraction
2. Add OCR fallback with Tesseract for scanned PDFs
3. Build data extraction patterns for common invoice formats
4. Create structured data models (vendor, date, amount, currency)
5. Implement validation and error handling
6. Store raw extracted text for debugging

**Deliverable**: System extracts key fields from various invoice formats

**Critical Files**:
- `app/invoices/pdf_parser.py`
- `tests/test_pdf_parser.py`

### Phase 4: AI Categorization
**Goal**: Automatically categorize invoices using Claude API

**Tasks**:
1. Integrate Claude API (Anthropic)
2. Design categorization prompt with examples
3. Implement category extraction and validation
4. Add confidence scoring
5. Create fallback rule-based categorization
6. Seed default categories (Office Supplies, Travel, Software, Professional Services, etc.)

**Deliverable**: Invoices are automatically categorized with confidence scores

**Critical Files**:
- `app/invoices/categorizer.py`
- `tests/test_categorizer.py`

### Phase 5: Background Processing
**Goal**: Handle batch processing asynchronously with Celery

**Tasks**:
1. Set up Celery with Redis broker
2. Create background tasks for batch processing
3. Implement progress tracking and status updates
4. Add real-time progress display with HTMX
5. Build retry logic for failed extractions
6. Create processing status page

**Deliverable**: Large batches process in background with progress tracking

**Critical Files**:
- `app/invoices/tasks.py`
- `celery_worker.py`
- `app/templates/invoices/processing.html`

### Phase 6: Summary & Visualization
**Goal**: Display insights and summaries

**Tasks**:
1. Build summary calculation logic (total amount, invoice count, date range)
2. Create dashboard with key metrics
3. Implement category breakdown with Chart.js
4. Build detailed categorized list view
5. Add sorting and filtering
6. Implement search functionality

**Deliverable**: Rich dashboard showing invoice insights

**Critical Files**:
- `app/templates/invoices/summary.html`
- `app/templates/invoices/details.html`
- `app/static/js/app.js`

### Phase 7: Export Functionality
**Goal**: Export data to CSV and Google Sheets

**Tasks**:
1. Implement CSV export with pandas
2. Add customizable column selection
3. Build Google Sheets integration with gspread
4. Create new sheet or append to existing
5. Add formatting for Sheets export
6. Implement download functionality

**Deliverable**: Users can export data to CSV or Google Sheets

**Critical Files**:
- `app/exports/csv_exporter.py`
- `app/exports/sheets_uploader.py`
- `app/exports/routes.py`

### Phase 8: Polish & Testing
**Goal**: Production-ready application

**Tasks**:
1. Comprehensive error handling and user feedback
2. Add loading states and animations
3. Write unit tests for core functionality
4. Write integration tests for workflows
5. Add sample invoice fixtures for testing
6. Create README with setup instructions
7. Document API endpoints

**Deliverable**: Tested, polished application ready for deployment

## Key Dependencies

```
# Core Framework
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-Login==0.6.3
Flask-WTF==1.2.1

# Database
psycopg2-binary==2.9.9

# Background Jobs
celery==5.3.4
redis==5.0.1

# Google APIs
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-api-python-client==2.110.0

# PDF Processing
pdfplumber==0.10.3
pytesseract==0.3.10
pdf2image==1.16.3
Pillow==10.1.0

# AI
anthropic==0.18.1

# Data Processing
pandas==2.1.4

# Google Sheets
gspread==5.12.3

# Utilities
python-dotenv==1.0.0
requests==2.31.0
validators==0.22.0
```

## API Endpoints

### Authentication
- `GET /auth/login` - Initiate Google OAuth
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout user

### Invoice Processing
- `GET /` - Landing page
- `GET /dashboard` - User dashboard
- `POST /invoices/process` - Submit Drive URL for processing
- `GET /invoices/batch/<id>` - Get batch status
- `GET /invoices/batch/<id>/summary` - Summary view
- `GET /invoices/batch/<id>/details` - Detailed categorized list
- `PUT /invoices/<id>/category` - Update invoice category
- `DELETE /invoices/batch/<id>` - Delete batch

### Export
- `GET /export/csv/<batch_id>` - Download CSV
- `POST /export/sheets/<batch_id>` - Upload to Google Sheets

## Environment Variables

```bash
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@db:5432/invoice_app
REDIS_URL=redis://redis:6379/0

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key
```

## Security Considerations

1. **OAuth 2.0 only** - No password storage
2. **Token encryption** - Encrypt refresh tokens at rest
3. **CSRF protection** - Flask-WTF for form protection
4. **Input validation** - Validate all Drive URLs
5. **SQL injection prevention** - Use SQLAlchemy ORM exclusively
6. **XSS protection** - Jinja2 auto-escaping enabled
7. **File validation** - Verify PDF MIME types and size limits
8. **Minimal Drive scopes** - Request drive.readonly only

## Local Development Setup

### Prerequisites
- Docker and Docker Compose installed
- Google Cloud Console project with OAuth credentials
- Anthropic API key

### Setup Steps
1. Clone repository
2. Copy `.env.example` to `.env` and fill in credentials
3. Run `docker-compose up --build`
4. Access application at `http://localhost:5000`
5. Run migrations: `docker-compose exec web flask db upgrade`

### Running Tests
```bash
docker-compose exec web pytest tests/
```

## Verification & Testing

### End-to-End Test Flow
1. **Authentication**: Navigate to `http://localhost:5000`, click "Login with Google", verify OAuth flow completes
2. **Drive Integration**: Paste a Google Drive folder URL with sample PDFs, verify files are listed
3. **Processing**: Submit batch for processing, verify progress bar updates in real-time
4. **Summary View**: Check summary shows correct totals, invoice count, date range, and category breakdown chart
5. **Details View**: Verify invoices are organized by category with all extracted fields visible
6. **Export CSV**: Download CSV, verify all data is present and properly formatted
7. **Export Sheets**: Upload to Google Sheets, verify new sheet is created with formatted data
8. **Error Handling**: Test with invalid Drive URL, verify error message displays
9. **Manual Categorization**: Change an invoice category, verify it updates and summary recalculates

### Unit Test Coverage
- PDF extraction with various formats
- OCR fallback logic
- AI categorization with mock responses
- Drive URL parsing
- CSV generation
- Google Sheets formatting

## Future Deployment Considerations

When ready to deploy, the application is designed to work with:
- **Render.com** (free tier with GitHub integration)
- **Railway.app** (free $5/month credit)
- **Heroku** (easy deployment)
- **AWS/DigitalOcean** (scalable production)

The Docker Compose setup can be adapted to any container-based hosting platform.

## Critical Files Summary

The 5 most critical files that form the backbone:

1. **app/__init__.py** - Flask application factory, initializes all extensions
2. **app/models.py** - Database models defining core data structure
3. **app/invoices/pdf_parser.py** - PDF extraction logic (core functionality)
4. **app/invoices/categorizer.py** - AI-powered categorization (key value-add)
5. **app/invoices/tasks.py** - Celery background tasks (scalability)

Once these are implemented, remaining components (routes, templates, exports) build on this foundation.
