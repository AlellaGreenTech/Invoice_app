# Quick Start Guide

## Prerequisites Checklist

Before starting, ensure you have:
- [ ] Docker and Docker Compose installed
- [ ] Google Cloud Console account
- [ ] Anthropic API account
- [ ] A Google Drive folder with sample PDF invoices

## 5-Minute Setup

### Step 1: Configure Google OAuth (5 minutes)

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Navigate to "APIs & Services" > "Library"
4. Enable these APIs:
   - Google Drive API
   - Google Sheets API
5. Go to "APIs & Services" > "Credentials"
6. Click "Create Credentials" > "OAuth 2.0 Client ID"
7. Configure OAuth consent screen (if needed):
   - User Type: External
   - App name: Invoice Processor
   - User support email: your email
   - Scopes: Add Drive and Sheets scopes
8. Create OAuth Client ID:
   - Application type: Web application
   - Name: Invoice Processor
   - Authorized redirect URIs: `http://localhost:5000/auth/callback`
9. Copy Client ID and Client Secret

### Step 2: Get Anthropic API Key (2 minutes)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to "API Keys"
4. Click "Create Key"
5. Copy the API key

### Step 3: Configure Environment (1 minute)

Edit `/Users/phoenixxu/agt/invoice_app/.env`:

```bash
# Replace these with your actual credentials
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Generate a secure secret key (run this command):
# python3 -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=your-generated-secret-key-here
```

### Step 4: Start the Application (2 minutes)

```bash
cd /Users/phoenixxu/agt/invoice_app

# Build and start all services
docker-compose up --build -d

# Wait for services to be ready (about 30 seconds)
docker-compose logs -f web

# In another terminal, initialize database
docker-compose exec web flask db upgrade

# Seed default categories
docker-compose exec web flask seed-categories
```

### Step 5: Test the Application (5 minutes)

1. Open browser: http://localhost:5000
2. Click "Sign in with Google"
3. Authorize the application
4. You should see the dashboard

## Testing with Sample Data

### Prepare Test Invoices

1. Create a Google Drive folder
2. Upload 3-5 sample PDF invoices
3. Share the folder (make sure you have access)
4. Copy the folder URL

### Process Your First Batch

1. Click "Upload Invoices" or "New Batch"
2. Paste your Google Drive folder URL
3. Click "Start Processing"
4. Watch the progress bar
5. View the summary dashboard
6. Explore the detailed invoice list
7. Export to CSV or Google Sheets

## Verification Checklist

After setup, verify:
- [ ] Can access http://localhost:5000
- [ ] Can log in with Google
- [ ] Dashboard loads without errors
- [ ] Can access upload page
- [ ] Services are running:
  ```bash
  docker-compose ps
  # Should show: web, db, redis, celery all "Up"
  ```

## Common Setup Issues

### Issue: OAuth redirect_uri_mismatch

**Solution**:
- Go to Google Cloud Console > Credentials
- Edit your OAuth 2.0 Client ID
- Ensure redirect URI is exactly: `http://localhost:5000/auth/callback`
- No trailing slash, no extra spaces

### Issue: Database connection error

**Solution**:
```bash
# Check if PostgreSQL is ready
docker-compose logs db | grep "ready to accept connections"

# Restart if needed
docker-compose restart db
docker-compose exec web flask db upgrade
```

### Issue: Celery worker not processing

**Solution**:
```bash
# Check Celery logs
docker-compose logs celery

# Restart Celery
docker-compose restart celery

# Verify Redis is running
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Issue: "Anthropic API key not configured"

**Solution**:
- Verify `.env` has `ANTHROPIC_API_KEY=sk-ant-...`
- Restart services: `docker-compose restart web celery`
- Check logs: `docker-compose logs web | grep ANTHROPIC`

### Issue: Can't access Google Drive folder

**Solution**:
- Ensure folder is shared with your Google account
- Try accessing the folder in a browser first
- Check folder URL format is correct
- Verify Drive API is enabled in Google Console

## Development Commands

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f web
docker-compose logs -f celery

# Restart a service
docker-compose restart web

# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v

# Run tests
docker-compose exec web pytest

# Access database
docker-compose exec db psql -U invoice_user -d invoice_app

# Access Python shell
docker-compose exec web flask shell

# Run migrations
docker-compose exec web flask db migrate -m "description"
docker-compose exec web flask db upgrade
```

## Sample Invoice URLs for Testing

If you don't have invoices ready, you can:

1. **Create sample invoices**: Use any PDF invoice template
2. **Use test data**: Create simple text-based PDFs with:
   - Company name at top
   - "Invoice #: INV-001"
   - "Date: 2024-01-15"
   - "Total: $1,234.56"

3. **Upload to Drive**:
   - Create a folder: "Test Invoices"
   - Upload 3-5 PDFs
   - Get the folder URL

## Next Steps After Setup

1. **Process your first batch** of invoices
2. **Review the categorization** accuracy
3. **Adjust categories** manually if needed
4. **Export results** to CSV or Sheets
5. **Test with larger batches** (50+ invoices)

## Production Deployment

When ready to deploy to production:

1. **Choose a platform**:
   - Render.com (easiest, free tier)
   - Railway.app ($5/month credit)
   - Heroku (simple deployment)
   - AWS/DigitalOcean (most control)

2. **Update environment**:
   - Use production database URL
   - Use production Redis URL
   - Update redirect URI in Google Console
   - Enable HTTPS

3. **Security checklist**:
   - Rotate SECRET_KEY
   - Enable token encryption
   - Set up monitoring
   - Configure backups
   - Enable rate limiting

## Support Resources

- **README.md**: Comprehensive documentation
- **SETUP_COMPLETE.md**: Implementation details
- **Docker logs**: `docker-compose logs -f`
- **Flask shell**: `docker-compose exec web flask shell`
- **Database**: `docker-compose exec db psql -U invoice_user -d invoice_app`

## Success Indicators

You'll know setup is successful when:
✅ All Docker services show "Up" status
✅ Can log in with Google OAuth
✅ Dashboard displays without errors
✅ Can upload and process a test batch
✅ Summary shows charts and statistics
✅ Can export to CSV successfully
✅ Tests pass: `docker-compose exec web pytest`

---

**Ready to process invoices!** 🚀

If you encounter any issues, check the logs first:
```bash
docker-compose logs -f
```
