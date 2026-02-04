# Invoice Processing Web Application

A web application for CFOs to process invoices from Google Drive, automatically categorize them using AI, and export organized summaries to CSV or Google Sheets.

## Features

- **Google Drive Integration**: Upload invoices directly from Google Drive folders
- **AI-Powered Categorization**: Automatic invoice categorization using Claude API
- **PDF Processing**: Extract data from PDFs with OCR fallback for scanned documents
- **Background Processing**: Handle large batches (50-200 invoices) asynchronously
- **Visual Summaries**: Dashboard with charts and category breakdowns
- **Export Options**: Download as CSV or export directly to Google Sheets

## Technology Stack

- **Backend**: Flask 3.x, PostgreSQL, Celery, Redis
- **Frontend**: Bootstrap 5, HTMX, Chart.js
- **PDF Processing**: pdfplumber, pytesseract
- **AI**: Anthropic Claude API
- **Google APIs**: Drive API, Sheets API, OAuth2

## Prerequisites

- Docker and Docker Compose
- Google Cloud Console project with OAuth credentials
- Anthropic API key

## Setup Instructions

### 1. Clone the Repository

```bash
cd /Users/phoenixxu/agt/invoice_app
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# Google OAuth - Get from Google Cloud Console
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback

# Anthropic Claude API
ANTHROPIC_API_KEY=your-anthropic-api-key

# Generate a secure secret key
SECRET_KEY=your-secure-secret-key-here
```

### 3. Set Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Sheets API
4. Create OAuth 2.0 credentials:
   - Application type: Web application
   - Authorized redirect URIs: `http://localhost:5000/auth/callback`
5. Copy the Client ID and Client Secret to your `.env` file

### 4. Get Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Generate an API key
3. Add it to your `.env` file

### 5. Build and Run with Docker

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

This will start:
- **Flask web server** on `http://localhost:5000`
- **PostgreSQL database** on port 5432
- **Redis** on port 6379
- **Celery worker** for background processing

### 6. Initialize the Database

```bash
# Run database migrations
docker-compose exec web flask db upgrade

# (Optional) Seed default categories
docker-compose exec web flask seed-categories
```

### 7. Access the Application

Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

### Processing Invoices

1. **Login**: Click "Sign in with Google" and authorize the application
2. **Upload**: Navigate to the upload page and paste a Google Drive folder URL
3. **Process**: The system will:
   - Download PDFs from the folder
   - Extract invoice data (vendor, date, amount, currency)
   - Categorize each invoice using AI
   - Generate summary statistics
4. **Review**: View the summary dashboard with charts and breakdowns
5. **Export**: Download as CSV or export to Google Sheets

### Google Drive URL Format

The application accepts Google Drive folder URLs in these formats:
```
https://drive.google.com/drive/folders/FOLDER_ID
https://drive.google.com/drive/u/0/folders/FOLDER_ID
```

Make sure the folder is shared with your Google account.

## Development

### Project Structure

```
invoice_app/
├── app/                    # Application code
│   ├── auth/              # Authentication routes
│   ├── invoices/          # Invoice processing logic
│   ├── exports/           # Export functionality
│   ├── static/            # CSS, JS files
│   ├── templates/         # Jinja2 templates
│   └── utils/             # Utility functions
├── tests/                 # Test files
├── docker-compose.yml     # Docker services
├── Dockerfile            # Container definition
└── requirements.txt      # Python dependencies
```

### Running Tests

```bash
# Run all tests
docker-compose exec web pytest

# Run with coverage
docker-compose exec web pytest --cov=app tests/

# Run specific test file
docker-compose exec web pytest tests/test_pdf_parser.py
```

### Database Migrations

```bash
# Create a new migration
docker-compose exec web flask db migrate -m "Description"

# Apply migrations
docker-compose exec web flask db upgrade

# Rollback migration
docker-compose exec web flask db downgrade
```

### Viewing Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f web
docker-compose logs -f celery
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
- `GET /invoices/batch/<id>/details` - Detailed list
- `PUT /invoices/<id>/category` - Update category
- `DELETE /invoices/batch/<id>` - Delete batch

### Export
- `GET /export/csv/<batch_id>` - Download CSV
- `POST /export/sheets/<batch_id>` - Upload to Google Sheets

## Troubleshooting

### Common Issues

**OAuth Error: redirect_uri_mismatch**
- Ensure the redirect URI in Google Cloud Console matches exactly: `http://localhost:5000/auth/callback`

**Database Connection Error**
- Wait for PostgreSQL to be ready (check with `docker-compose logs db`)
- Verify DATABASE_URL in `.env`

**Celery Tasks Not Running**
- Check Celery worker logs: `docker-compose logs celery`
- Verify Redis is running: `docker-compose ps redis`

**PDF Extraction Fails**
- Ensure Tesseract is installed in the container
- Check PDF file is not corrupted or password-protected

### Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (deletes database data)
docker-compose down -v
```

## Security Considerations

- OAuth tokens are stored in the database (should be encrypted in production)
- CSRF protection enabled for all forms
- SQL injection prevention via SQLAlchemy ORM
- Input validation for all user inputs
- Minimal Google Drive scopes (read-only access)

## Future Enhancements

- [ ] Multi-currency support with conversion
- [ ] Custom category management
- [ ] Batch comparison and analytics
- [ ] Email notifications for completed batches
- [ ] Duplicate invoice detection
- [ ] Multi-user organization support
- [ ] Cloud deployment (Render, Railway, AWS)

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.

---

Built with Flask and Claude AI
