# Glossary

Terms and concepts used in Invoice Processor.

---

## A

**API (Application Programming Interface)**
- Interface for programmatic access to the application
- See API.md for complete documentation

**Anthropic**
- Company that created Claude AI
- Provides the AI API used for categorization

**Authentication**
- Process of verifying user identity
- Uses Google OAuth 2.0

**Authorization**
- Process of verifying user permissions
- Checks if user can access specific resources

---

## B

**Batch**
- A collection of invoices processed together
- Typically 50-200 invoices
- Has status: pending, processing, completed, or failed

**Background Processing**
- Tasks that run asynchronously
- Handled by Celery workers
- Allows processing without blocking the UI

**Bootstrap**
- CSS framework used for UI design
- Version 5 used in this project

---

## C

**Celery**
- Distributed task queue system
- Handles background invoice processing
- Uses Redis as message broker

**Category**
- Classification of invoice type
- Examples: Office Supplies, Travel, Software
- 16 default categories provided

**Categorization**
- Process of assigning category to invoice
- Uses Claude AI for automatic categorization
- Can be manually updated by user

**Claude**
- AI model by Anthropic
- Used for invoice categorization
- Sonnet 4.5 version used

**Confidence Score**
- Measure of AI's certainty (0-100%)
- Higher score = more confident categorization
- Displayed as percentage

**CSV (Comma-Separated Values)**
- File format for data export
- Can be opened in Excel or Google Sheets
- One of two export formats supported

**CSRF (Cross-Site Request Forgery)**
- Security attack type
- Protection enabled on all forms
- Prevents unauthorized actions

---

## D

**Dashboard**
- Main user interface after login
- Shows recent batches and statistics
- Entry point for most actions

**Database**
- PostgreSQL database
- Stores users, batches, invoices, categories
- Runs in Docker container

**Docker**
- Containerization platform
- Used for local development
- Ensures consistent environment

**Docker Compose**
- Tool for multi-container Docker applications
- Orchestrates web, database, Redis, Celery
- Configured in docker-compose.yml

**Drive (Google Drive)**
- Cloud storage service by Google
- Source of PDF invoices
- Accessed via Drive API

---

## E

**Environment Variables**
- Configuration values stored in .env file
- Includes API keys and secrets
- Never committed to version control

**Export**
- Process of downloading processed data
- Two formats: CSV and Google Sheets
- Includes all invoice data and summary

**Extraction**
- Process of getting data from PDF
- Extracts vendor, date, amount, currency
- Uses pdfplumber or OCR

---

## F

**Flask**
- Python web framework
- Version 3.0 used
- Handles HTTP requests and responses

---

## G

**Google Sheets**
- Online spreadsheet application
- One of two export formats
- Automatically formatted with headers

---

## H

**Health Check**
- Endpoint to verify application status
- Returns JSON with status information
- Used for monitoring

**HTMX**
- JavaScript library for dynamic updates
- Enables real-time progress tracking
- Minimal JavaScript required

---

## I

**Invoice**
- Individual bill or receipt
- Extracted from PDF file
- Contains vendor, date, amount, category

**Invoice Number**
- Unique identifier on invoice
- Extracted from PDF
- May not always be present

---

## J

**Jinja2**
- Template engine for Python
- Used for HTML templates
- Provides auto-escaping for security

**JSON (JavaScript Object Notation)**
- Data format for API responses
- Human-readable text format
- Used for AJAX requests

---

## M

**Migration**
- Database schema change
- Managed by Flask-Migrate
- Allows versioned database updates

---

## O

**OAuth (Open Authorization)**
- Authentication protocol
- Version 2.0 used
- Allows login with Google account

**OCR (Optical Character Recognition)**
- Technology to extract text from images
- Used for scanned PDFs
- Fallback when pdfplumber fails

**ORM (Object-Relational Mapping)**
- SQLAlchemy ORM used
- Maps Python objects to database tables
- Prevents SQL injection

---

## P

**PDF (Portable Document Format)**
- File format for invoices
- Only format currently supported
- Can be text-based or scanned

**pdfplumber**
- Python library for PDF text extraction
- Primary extraction method
- Falls back to OCR if insufficient text

**PostgreSQL**
- Relational database system
- Version 15 used
- Stores all application data

**Progress Tracking**
- Real-time updates during processing
- Shows percentage complete
- Updates via HTMX

**pytesseract**
- Python wrapper for Tesseract OCR
- Used for scanned PDFs
- Fallback extraction method

---

## R

**Redis**
- In-memory data store
- Used as Celery message broker
- Also used for caching

**REST API**
- Architectural style for APIs
- Used for all API endpoints
- Returns JSON responses

---

## S

**Session**
- User's authenticated state
- Stored in secure cookies
- Expires after 7 days

**SQLAlchemy**
- Python SQL toolkit and ORM
- Version 3.1 used
- Handles all database operations

**Summary**
- Overview of batch processing results
- Includes charts and statistics
- Shows category breakdown

---

## T

**Task**
- Unit of work in Celery
- Example: processing one batch
- Can be monitored and retried

**Template**
- HTML file with Jinja2 syntax
- Rendered with data from Flask
- Located in app/templates/

**Token**
- OAuth access token
- Used for API authentication
- Automatically refreshed when expired

---

## U

**User**
- Person using the application
- Authenticated via Google OAuth
- Can have multiple batches

---

## V

**Vendor**
- Company that issued the invoice
- Extracted from PDF
- Used for identification

**Visualization**
- Charts and graphs
- Created with Chart.js
- Shows category breakdown

---

## W

**Worker**
- Celery worker process
- Processes background tasks
- Can be scaled horizontally

---

## X

**XSS (Cross-Site Scripting)**
- Security attack type
- Protection via Jinja2 auto-escaping
- Prevents malicious script injection

---

## Common Acronyms

- **API**: Application Programming Interface
- **CLI**: Command Line Interface
- **CPU**: Central Processing Unit
- **CSRF**: Cross-Site Request Forgery
- **CSV**: Comma-Separated Values
- **DB**: Database
- **ENV**: Environment
- **FAQ**: Frequently Asked Questions
- **GB**: Gigabyte
- **HTTP**: Hypertext Transfer Protocol
- **HTTPS**: HTTP Secure
- **ID**: Identifier
- **JSON**: JavaScript Object Notation
- **JWT**: JSON Web Token
- **KB**: Kilobyte
- **MB**: Megabyte
- **OCR**: Optical Character Recognition
- **ORM**: Object-Relational Mapping
- **OS**: Operating System
- **PDF**: Portable Document Format
- **RAM**: Random Access Memory
- **REST**: Representational State Transfer
- **RPO**: Recovery Point Objective
- **RTO**: Recovery Time Objective
- **SQL**: Structured Query Language
- **SSL**: Secure Sockets Layer
- **TLS**: Transport Layer Security
- **UI**: User Interface
- **URL**: Uniform Resource Locator
- **UUID**: Universally Unique Identifier
- **VPC**: Virtual Private Cloud
- **XSS**: Cross-Site Scripting

---

## Technical Terms

**Async/Asynchronous**
- Operations that don't block execution
- Used for background processing
- Improves performance

**Container**
- Isolated environment for running applications
- Docker containers used
- Ensures consistency

**Endpoint**
- URL that accepts API requests
- Example: /api/batches/1
- Returns JSON response

**Hook**
- Code that runs at specific events
- Pre-commit hooks available
- Used for automation

**Middleware**
- Software between request and response
- Handles authentication, logging, etc.
- Part of Flask architecture

**Schema**
- Structure of database tables
- Defined in models.py
- Managed via migrations

**Webhook**
- HTTP callback for events
- Not currently implemented
- Planned for future version

---

## Status Values

**Batch Status**
- `pending`: Waiting to start
- `processing`: Currently processing
- `completed`: Successfully finished
- `failed`: Processing failed

**Invoice Status**
- `pending`: Not yet processed
- `extracted`: Data extracted from PDF
- `categorized`: Category assigned
- `failed`: Processing failed

---

## File Extensions

- `.py`: Python source code
- `.html`: HTML template
- `.md`: Markdown documentation
- `.txt`: Plain text file
- `.sql`: SQL script
- `.json`: JSON data file
- `.yml`/`.yaml`: YAML configuration
- `.env`: Environment variables
- `.sh`: Shell script
- `.pdf`: PDF document
- `.csv`: CSV data file
- `.log`: Log file

---

*Glossary v1.0.0*
*Last Updated: 2026-02-03*
