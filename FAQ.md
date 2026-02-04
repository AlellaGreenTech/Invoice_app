# Frequently Asked Questions (FAQ)

## General Questions

### What is Invoice Processor?
Invoice Processor is a web application that automatically processes PDF invoices from Google Drive, extracts data, categorizes them using AI, and exports results to CSV or Google Sheets.

### Who is this for?
This application is designed for CFOs, accountants, and finance teams who need to process large batches of invoices (50-200+) efficiently.

### How much does it cost?
The application itself is free and open-source (MIT License). You only pay for:
- Google Cloud APIs (free tier available)
- Anthropic Claude API (pay-per-use)
- Hosting costs (if deploying to cloud)

---

## Setup & Installation

### Q: What are the system requirements?
**A:** You need:
- Docker and Docker Compose installed
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space
- Internet connection for API calls

### Q: How do I get Google OAuth credentials?
**A:**
1. Go to https://console.cloud.google.com/
2. Create a new project
3. Enable Google Drive API and Google Sheets API
4. Create OAuth 2.0 Client ID (Web application)
5. Add redirect URI: `http://localhost:5000/auth/callback`
6. Copy Client ID and Client Secret to `.env`

### Q: How do I get an Anthropic API key?
**A:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new key
5. Copy to `.env` file

### Q: The setup script fails. What should I do?
**A:**
1. Check Docker is running: `docker ps`
2. Check logs: `docker-compose logs -f`
3. Verify `.env` file exists and has correct values
4. Try manual setup steps in QUICKSTART.md
5. Run verification: `./verify.sh`

### Q: How do I know if setup was successful?
**A:**
Run `./verify.sh` or check:
- All services are "Up": `docker-compose ps`
- Can access http://localhost:5000
- Can log in with Google
- Tests pass: `make test`

---

## Usage Questions

### Q: What file formats are supported?
**A:** Currently only PDF files are supported. The application can handle:
- Text-based PDFs (preferred)
- Scanned PDFs (using OCR)
- Mixed content PDFs

### Q: How many invoices can I process at once?
**A:** The application is designed to handle 50-200 invoices per batch. You can process more, but it may take longer.

### Q: How long does processing take?
**A:** Processing time depends on:
- Number of invoices
- PDF complexity (text vs scanned)
- API response times
- Typically: 1-2 seconds per invoice

### Q: Can I process invoices from my local computer?
**A:** No, invoices must be in Google Drive. This is by design for security and to leverage Google's infrastructure.

### Q: What if the AI categorizes an invoice incorrectly?
**A:** You can manually update the category:
1. Go to the batch details page
2. Click the edit button next to the invoice
3. Select the correct category
4. The change is saved immediately

### Q: Can I add custom categories?
**A:** Currently, you can manually assign any category name when editing. Custom category management UI is planned for a future version.

---

## Technical Questions

### Q: What database does it use?
**A:** PostgreSQL 15. The database runs in a Docker container for local development.

### Q: How is background processing handled?
**A:** Using Celery with Redis as the message broker. This allows processing large batches without blocking the web interface.

### Q: Is my data secure?
**A:** Yes:
- OAuth 2.0 authentication (no passwords stored)
- CSRF protection on all forms
- SQL injection prevention via ORM
- XSS protection with auto-escaping
- Minimal API scopes (read-only Drive access)

### Q: Where are the PDFs stored?
**A:** PDFs are downloaded temporarily to `/tmp/invoices` during processing and deleted after extraction. Only the extracted data is stored in the database.

### Q: Can I run this without Docker?
**A:** Yes, but it's not recommended. You would need to:
- Install PostgreSQL and Redis locally
- Set up Python virtual environment
- Install all dependencies
- Configure services manually

### Q: How do I backup my data?
**A:**
```bash
# Backup database
docker-compose exec db pg_dump -U invoice_user invoice_app > backup.sql

# Restore database
docker-compose exec -T db psql -U invoice_user invoice_app < backup.sql
```

---

## API & Integration

### Q: Is there an API?
**A:** Yes, see API.md for complete documentation. The API includes endpoints for:
- Batch status
- Invoice management
- Category updates
- Export operations

### Q: Can I integrate this with other systems?
**A:** Yes, you can use the REST API to integrate with other systems. Authentication is via session cookies (OAuth).

### Q: Does it support webhooks?
**A:** Not currently, but this is planned for a future version.

---

## Troubleshooting

### Q: "OAuth redirect_uri_mismatch" error
**A:** The redirect URI in Google Console must exactly match:
```
http://localhost:5000/auth/callback
```
No trailing slash, no extra spaces.

### Q: "Database connection error"
**A:**
```bash
# Check if PostgreSQL is running
docker-compose logs db | grep "ready to accept connections"

# Restart database
docker-compose restart db

# Run migrations
docker-compose exec web flask db upgrade
```

### Q: "Celery worker not processing tasks"
**A:**
```bash
# Check Celery logs
docker-compose logs celery

# Verify Redis is running
docker-compose exec redis redis-cli ping

# Restart Celery
docker-compose restart celery
```

### Q: "Failed to extract text from PDF"
**A:** This can happen with:
- Encrypted/password-protected PDFs
- Corrupted PDF files
- Very complex layouts

Try:
- Ensure PDF is not encrypted
- Try a different PDF
- Check logs for specific error

### Q: Application is slow
**A:** Check:
- Docker resource allocation (increase if needed)
- Number of concurrent batches
- Database size (consider cleanup)
- Redis memory usage

---

## Export & Data

### Q: What format is the CSV export?
**A:** Standard CSV with columns:
- Invoice Number
- Vendor Name
- Invoice Date
- Amount
- Currency
- Category
- Confidence
- Filename
- Status

### Q: Can I customize the CSV columns?
**A:** Yes, the CSV exporter supports custom column selection (see API.md).

### Q: How does Google Sheets export work?
**A:** The application:
1. Creates a new spreadsheet (or adds to existing)
2. Formats headers with colors
3. Adds all invoice data
4. Includes summary section
5. Returns the spreadsheet URL

### Q: Can I export to Excel?
**A:** Not directly, but you can:
- Export to CSV and open in Excel
- Export to Google Sheets and download as Excel

---

## Performance & Scaling

### Q: How many users can use this simultaneously?
**A:** For local development: 1-5 users
For production: Depends on hosting resources, but can scale horizontally.

### Q: Can I process multiple batches at once?
**A:** Yes, Celery handles multiple batches concurrently. The number depends on worker configuration.

### Q: How do I scale for production?
**A:** See DEPLOYMENT.md for:
- Horizontal scaling (multiple workers)
- Database optimization
- Redis scaling
- Load balancing

---

## Deployment

### Q: Can I deploy this to production?
**A:** Yes! See DEPLOYMENT.md for guides on:
- Render.com (easiest)
- Railway.app (recommended)
- Heroku
- AWS/DigitalOcean

### Q: What's the easiest deployment option?
**A:** Render.com offers:
- Free tier available
- Automatic HTTPS
- Easy setup
- GitHub integration

### Q: Do I need to change anything for production?
**A:** Yes:
- Update SECRET_KEY
- Use production database
- Update OAuth redirect URI
- Enable HTTPS
- Set up monitoring
- Configure backups

---

## Costs

### Q: What are the ongoing costs?
**A:**
- **Google APIs**: Free tier covers most usage
- **Anthropic Claude**: ~$0.003 per invoice (varies)
- **Hosting**: $0-50/month depending on platform
- **Total**: ~$10-50/month for moderate usage

### Q: How can I reduce costs?
**A:**
- Use free tier hosting (Render.com)
- Optimize API calls
- Use rule-based categorization as fallback
- Process in larger batches

---

## Future Features

### Q: What features are planned?
**A:** See CHANGELOG.md for roadmap:
- Multi-currency conversion
- Custom category management UI
- Duplicate detection
- Email notifications
- Batch comparison
- Mobile app

### Q: Can I request a feature?
**A:** Yes! See CONTRIBUTING.md for how to:
- Open a feature request
- Submit a pull request
- Contribute to development

### Q: Is there a paid/enterprise version?
**A:** Not currently. The application is open-source and free to use.

---

## Support

### Q: Where can I get help?
**A:**
1. Check this FAQ
2. Read the documentation (14 guides)
3. Check logs: `docker-compose logs -f`
4. Run verification: `./verify.sh`
5. Open an issue on GitHub

### Q: How do I report a bug?
**A:** See CONTRIBUTING.md for bug report guidelines.

### Q: Can I hire someone to set this up?
**A:** The application is designed to be self-service, but you can hire a developer familiar with Flask/Docker.

---

## Miscellaneous

### Q: What's the difference between this and other invoice processors?
**A:** This application:
- Is open-source and free
- Uses AI for categorization
- Integrates with Google Drive
- Handles batch processing
- Provides visual dashboards
- Exports to multiple formats

### Q: Can I use this commercially?
**A:** Yes, the MIT License allows commercial use.

### Q: How do I contribute?
**A:** See CONTRIBUTING.md for guidelines on:
- Code contributions
- Documentation improvements
- Bug reports
- Feature requests

### Q: Is there a demo?
**A:** You can run it locally following the QUICKSTART.md guide. A hosted demo is not currently available.

---

## Still Have Questions?

- **Documentation**: Check the 14 comprehensive guides
- **Logs**: `docker-compose logs -f`
- **Verification**: `./verify.sh`
- **Community**: Open an issue on GitHub

---

*Last Updated: 2026-02-03*
*Version: 1.0.0*
