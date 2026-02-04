# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-02-03

### Added - Initial Release

#### Core Features
- **Google OAuth Authentication**
  - Secure login with Google accounts
  - Token management and automatic refresh
  - User session handling with Flask-Login

- **Google Drive Integration**
  - Parse and validate Google Drive URLs
  - List PDF files from folders
  - Download files for processing
  - Access control validation

- **PDF Processing**
  - Text extraction using pdfplumber
  - OCR fallback with Tesseract for scanned PDFs
  - Extract vendor name, invoice number, date, amount, currency
  - Pattern matching for various invoice formats
  - Support for multiple date and currency formats

- **AI-Powered Categorization**
  - Claude API integration (Sonnet 4.5)
  - 16 default categories
  - Confidence scoring (0-100%)
  - Rule-based fallback when API unavailable
  - Keyword matching system

- **Background Processing**
  - Celery + Redis for async batch processing
  - Real-time progress tracking
  - Handle 50-200 invoices per batch
  - Error handling and retry logic
  - Task status monitoring

- **Summary Dashboard**
  - Visual statistics with Chart.js
  - Category breakdown (doughnut chart)
  - Amount by category (bar chart)
  - Key metrics display
  - Date range analysis

- **Export Functionality**
  - CSV export with customizable columns
  - Google Sheets integration
  - Formatted spreadsheets with summary data
  - Direct download or cloud export
  - Summary-only sheet option

- **User Interface**
  - Responsive Bootstrap 5 design
  - HTMX for dynamic updates
  - Real-time progress indicators
  - Mobile-friendly layout
  - Custom CSS styling

#### Technical Implementation

- **Backend**
  - Flask 3.0 application factory pattern
  - PostgreSQL database with SQLAlchemy ORM
  - Flask-Migrate for database migrations
  - Celery 5.3 for background tasks
  - Redis for task queue and caching

- **Database Models**
  - User model with OAuth tokens
  - Batch model for processing jobs
  - Invoice model for individual invoices
  - Category model for categorization

- **Security**
  - OAuth 2.0 authentication only
  - CSRF protection on all forms
  - SQL injection prevention via ORM
  - XSS protection with Jinja2 auto-escaping
  - Input validation for all user inputs
  - Authorization checks on all routes

- **Testing**
  - Comprehensive test suite with pytest
  - Unit tests for all components
  - Integration tests for workflows
  - Test fixtures for common scenarios
  - Edge case testing

- **Documentation**
  - Complete README with setup instructions
  - Quick start guide
  - Implementation details document
  - API endpoint documentation
  - Troubleshooting guide

- **Development Tools**
  - Docker Compose for local development
  - Automated setup script
  - CLI commands for common tasks
  - Database migration tools
  - Test runner configuration

#### Default Categories

1. Office Supplies
2. Travel
3. Software & Technology
4. Professional Services
5. Utilities
6. Marketing & Advertising
7. Equipment & Hardware
8. Rent & Facilities
9. Insurance
10. Legal & Compliance
11. Training & Education
12. Meals & Entertainment
13. Telecommunications
14. Shipping & Delivery
15. Maintenance & Repairs
16. Other

#### API Endpoints

**Authentication**
- `GET /auth/login` - Initiate Google OAuth
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/logout` - Logout user

**Invoices**
- `GET /invoices/upload` - Upload form
- `POST /invoices/process` - Start processing
- `GET /invoices/processing/<id>` - Progress page
- `GET /invoices/batch/<id>` - Status API
- `GET /invoices/batch/<id>/summary` - Summary view
- `GET /invoices/batch/<id>/details` - Details view
- `PUT /invoices/<id>/category` - Update category
- `DELETE /invoices/batch/<id>` - Delete batch

**Exports**
- `GET /export/csv/<batch_id>` - Download CSV
- `POST /export/sheets/<batch_id>` - Export to Sheets
- `POST /export/sheets/<batch_id>/summary` - Export summary

#### CLI Commands

- `flask init-db` - Initialize database
- `flask seed-categories` - Seed default categories
- `flask reset-db` - Reset database
- `flask db upgrade` - Run migrations
- `flask db migrate` - Create migration

#### Environment Variables

- `FLASK_ENV` - Application environment
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `GOOGLE_REDIRECT_URI` - OAuth redirect URI
- `ANTHROPIC_API_KEY` - Claude API key
- `MAX_CONTENT_LENGTH` - Max file upload size
- `UPLOAD_FOLDER` - Temporary upload directory

#### Dependencies

**Core**
- Flask 3.0.0
- Flask-SQLAlchemy 3.1.1
- Flask-Migrate 4.0.5
- Flask-Login 0.6.3
- Flask-WTF 1.2.1

**Database**
- psycopg2-binary 2.9.9

**Background Jobs**
- celery 5.3.4
- redis 5.0.1

**Google APIs**
- google-auth 2.25.2
- google-auth-oauthlib 1.2.0
- google-api-python-client 2.110.0

**PDF Processing**
- pdfplumber 0.10.3
- pytesseract 0.3.10
- pdf2image 1.16.3
- Pillow 10.1.0

**AI**
- anthropic 0.18.1

**Data Processing**
- pandas 2.1.4

**Google Sheets**
- gspread 5.12.3

**Utilities**
- python-dotenv 1.0.0
- requests 2.31.0
- validators 0.22.0
- Werkzeug 3.0.1

### Project Statistics

- **Total Files**: 50+
- **Python Files**: 30
- **HTML Templates**: 11
- **Test Files**: 7
- **Lines of Code**: ~3,200
- **Documentation**: 4 comprehensive guides

### Known Limitations

- Single currency per batch (uses most common)
- No multi-tenant support yet
- Manual category editing one at a time
- No duplicate invoice detection
- No email notifications
- Limited to PDF format only

### Future Roadmap

#### Version 1.1 (Planned)
- Multi-currency conversion
- Custom category management UI
- Batch comparison analytics
- Email notifications
- Duplicate detection

#### Version 1.2 (Planned)
- Multi-tenant support
- Invoice approval workflow
- Advanced search and filters
- Audit trail
- Bulk category updates

#### Version 2.0 (Planned)
- Machine learning model training
- Custom extraction rules
- API for external integrations
- Mobile app
- Advanced reporting

### Contributors

- Initial implementation: Claude Sonnet 4.5

### License

MIT License

---

For detailed setup instructions, see [QUICKSTART.md](QUICKSTART.md)

For implementation details, see [SETUP_COMPLETE.md](SETUP_COMPLETE.md)

For usage documentation, see [README.md](README.md)
