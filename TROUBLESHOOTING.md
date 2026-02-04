# Troubleshooting Guide

Complete troubleshooting reference for Invoice Processor.

---

## Quick Diagnostics

### Run Verification Script
```bash
./verify.sh
```

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f db
docker-compose logs -f redis
```

---

## Common Issues

### 1. OAuth Authentication Errors

#### Error: "redirect_uri_mismatch"

**Symptoms:**
- Can't log in with Google
- Error message about redirect URI

**Cause:**
Redirect URI in Google Console doesn't match application configuration.

**Solution:**
1. Go to Google Cloud Console
2. Navigate to Credentials
3. Edit your OAuth 2.0 Client ID
4. Ensure redirect URI is exactly:
   ```
   http://localhost:5000/auth/callback
   ```
5. No trailing slash, no extra spaces
6. For production, update to your domain:
   ```
   https://yourdomain.com/auth/callback
   ```

**Verify:**
```bash
# Check .env file
grep GOOGLE_REDIRECT_URI .env
```

---

#### Error: "Access denied" or "Invalid client"

**Symptoms:**
- OAuth flow fails
- "Invalid client" error

**Cause:**
- Incorrect Client ID or Secret
- APIs not enabled

**Solution:**
1. Verify credentials in `.env`:
   ```bash
   cat .env | grep GOOGLE_CLIENT
   ```
2. Check Google Cloud Console:
   - Client ID matches
   - Client Secret matches
   - Drive API is enabled
   - Sheets API is enabled
3. Restart services:
   ```bash
   docker-compose restart web
   ```

---

### 2. Database Connection Errors

#### Error: "could not connect to server"

**Symptoms:**
- Application won't start
- Database connection errors in logs

**Cause:**
- PostgreSQL not ready
- Wrong connection string
- Port conflict

**Solution:**

**Check if PostgreSQL is running:**
```bash
docker-compose ps db
```

**Check PostgreSQL logs:**
```bash
docker-compose logs db | grep "ready to accept connections"
```

**Restart database:**
```bash
docker-compose restart db
sleep 5
docker-compose exec web flask db upgrade
```

**Verify connection string:**
```bash
grep DATABASE_URL .env
# Should be: postgresql://invoice_user:invoice_pass@db:5432/invoice_app
```

**Check for port conflicts:**
```bash
lsof -i :5432
# If another PostgreSQL is running, stop it or change port
```

---

#### Error: "relation does not exist"

**Symptoms:**
- Database errors about missing tables
- "relation 'users' does not exist"

**Cause:**
- Migrations not run
- Database not initialized

**Solution:**
```bash
# Run migrations
docker-compose exec web flask db upgrade

# Seed categories
docker-compose exec web flask seed-categories

# Verify tables exist
docker-compose exec db psql -U invoice_user -d invoice_app -c "\dt"
```

---

### 3. Celery Worker Issues

#### Error: "Celery worker not processing tasks"

**Symptoms:**
- Batches stuck in "pending" status
- No progress on invoice processing
- Worker logs show errors

**Cause:**
- Celery worker not running
- Redis connection issues
- Task errors

**Solution:**

**Check Celery worker status:**
```bash
docker-compose ps celery
```

**Check Celery logs:**
```bash
docker-compose logs celery | tail -50
```

**Verify Redis connection:**
```bash
docker-compose exec redis redis-cli ping
# Should return: PONG
```

**Restart Celery:**
```bash
docker-compose restart celery
```

**Check Redis URL:**
```bash
grep REDIS_URL .env
# Should be: redis://redis:6379/0
```

**Test task manually:**
```bash
docker-compose exec web flask shell
>>> from app.invoices.tasks import process_invoice_batch
>>> # Check if task is registered
```

---

#### Error: "Connection refused" to Redis

**Symptoms:**
- Celery can't connect to Redis
- "Error 111 connecting to redis:6379"

**Cause:**
- Redis not running
- Wrong Redis URL

**Solution:**
```bash
# Check Redis status
docker-compose ps redis

# Restart Redis
docker-compose restart redis

# Test connection
docker-compose exec web python -c "import redis; r = redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

---

### 4. PDF Processing Errors

#### Error: "Failed to extract text from PDF"

**Symptoms:**
- Invoice processing fails
- "Could not extract text" error

**Cause:**
- Encrypted PDF
- Corrupted file
- Unsupported format

**Solution:**

**Check PDF file:**
- Ensure PDF is not password-protected
- Try opening PDF in a viewer
- Verify file is not corrupted

**Check Tesseract installation:**
```bash
docker-compose exec web tesseract --version
```

**Check logs for specific error:**
```bash
docker-compose logs web | grep "PDF"
```

**Test PDF parser:**
```bash
docker-compose exec web python -c "
from app.invoices.pdf_parser import PDFParser
parser = PDFParser()
# Test with a sample PDF
"
```

---

#### Error: "OCR failed"

**Symptoms:**
- Scanned PDFs not processing
- OCR errors in logs

**Cause:**
- Tesseract not installed
- Poor image quality
- Unsupported language

**Solution:**
```bash
# Verify Tesseract is installed
docker-compose exec web which tesseract

# Check Tesseract languages
docker-compose exec web tesseract --list-langs

# Rebuild container if needed
docker-compose build web
docker-compose up -d
```

---

### 5. Google Drive Access Issues

#### Error: "Folder not found or not accessible"

**Symptoms:**
- Can't access Drive folder
- "Access denied" errors

**Cause:**
- Folder not shared with user
- Wrong folder URL
- Insufficient permissions

**Solution:**

**Verify folder URL format:**
```
https://drive.google.com/drive/folders/FOLDER_ID
```

**Check folder permissions:**
1. Open folder in Google Drive
2. Click "Share"
3. Ensure your Google account has access
4. Try "Anyone with the link" for testing

**Test Drive API access:**
```bash
docker-compose exec web flask shell
>>> from app.auth.google_auth import GoogleAuth
>>> from app.models import User
>>> user = User.query.first()
>>> # Test Drive access
```

---

#### Error: "Drive API not enabled"

**Symptoms:**
- "Drive API has not been used" error
- 403 Forbidden errors

**Cause:**
- Drive API not enabled in Google Console

**Solution:**
1. Go to Google Cloud Console
2. Navigate to "APIs & Services" > "Library"
3. Search for "Google Drive API"
4. Click "Enable"
5. Do the same for "Google Sheets API"
6. Wait a few minutes for changes to propagate

---

### 6. Application Performance Issues

#### Issue: Application is slow

**Symptoms:**
- Slow page loads
- Timeouts
- High CPU/memory usage

**Diagnosis:**
```bash
# Check Docker resource usage
docker stats

# Check service logs for errors
docker-compose logs -f

# Check database connections
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT count(*) FROM pg_stat_activity;"
```

**Solutions:**

**Increase Docker resources:**
- Docker Desktop > Settings > Resources
- Increase CPU and Memory allocation

**Optimize database:**
```bash
# Vacuum database
docker-compose exec db psql -U invoice_user -d invoice_app -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT pg_size_pretty(pg_database_size('invoice_app'));"
```

**Scale Celery workers:**
```yaml
# In docker-compose.yml
celery:
  command: celery -A celery_worker.celery worker --loglevel=info --concurrency=4
```

---

#### Issue: Out of memory errors

**Symptoms:**
- Container crashes
- "Out of memory" errors
- Services restart frequently

**Solution:**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Docker Desktop > Settings > Resources > Memory

# Reduce batch size
# Process fewer invoices per batch

# Clear old data
docker-compose exec web flask shell
>>> from app.models import Batch
>>> # Delete old batches
```

---

### 7. Export Issues

#### Error: "Failed to export to Google Sheets"

**Symptoms:**
- Sheets export fails
- Permission errors

**Cause:**
- Sheets API not enabled
- Insufficient permissions
- Token expired

**Solution:**
```bash
# Check Sheets API is enabled in Google Console

# Verify user has valid token
docker-compose exec web flask shell
>>> from app.models import User
>>> user = User.query.first()
>>> print(user.token_expiry)

# Re-authenticate if needed
# Log out and log back in
```

---

#### Error: "CSV export is empty"

**Symptoms:**
- CSV file downloads but is empty
- No data in export

**Cause:**
- No invoices in batch
- Query error

**Solution:**
```bash
# Check batch has invoices
docker-compose exec web flask shell
>>> from app.models import Batch, Invoice
>>> batch = Batch.query.get(1)
>>> print(batch.invoices.count())

# Check logs for errors
docker-compose logs web | grep "export"
```

---

### 8. Docker Issues

#### Error: "Cannot connect to Docker daemon"

**Symptoms:**
- Docker commands fail
- "Is the docker daemon running?"

**Solution:**
```bash
# Start Docker Desktop (macOS/Windows)
# Or start Docker service (Linux)
sudo systemctl start docker

# Verify Docker is running
docker ps
```

---

#### Error: "Port already in use"

**Symptoms:**
- "bind: address already in use"
- Can't start services

**Solution:**
```bash
# Find process using port
lsof -i :5000  # Web
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill process or change port in docker-compose.yml
```

---

#### Error: "No space left on device"

**Symptoms:**
- Can't build images
- Container crashes

**Solution:**
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune

# Check disk space
df -h
```

---

## Environment Issues

### Issue: Environment variables not loading

**Symptoms:**
- "Config not found" errors
- Default values being used

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check .env format (no spaces around =)
cat .env

# Restart services to reload
docker-compose down
docker-compose up -d

# Verify variables are loaded
docker-compose exec web env | grep GOOGLE
```

---

### Issue: Secret key errors

**Symptoms:**
- Session errors
- "Secret key not set"

**Solution:**
```bash
# Generate new secret key
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Add to .env
echo "SECRET_KEY=<generated-key>" >> .env

# Restart
docker-compose restart web
```

---

## Testing Issues

### Issue: Tests failing

**Symptoms:**
- pytest errors
- Import errors

**Solution:**
```bash
# Run tests with verbose output
docker-compose exec web pytest -v

# Run specific test
docker-compose exec web pytest tests/test_models.py -v

# Check test database
docker-compose exec web pytest --tb=short

# Rebuild if needed
docker-compose build web
```

---

## Network Issues

### Issue: Can't access application

**Symptoms:**
- http://localhost:5000 doesn't load
- Connection refused

**Solution:**
```bash
# Check services are running
docker-compose ps

# Check port mapping
docker-compose port web 5000

# Check firewall
# Ensure port 5000 is not blocked

# Try different browser
# Clear browser cache
```

---

## Data Issues

### Issue: Lost data after restart

**Symptoms:**
- Users/batches disappeared
- Database empty

**Cause:**
- Volume not persisted
- Database reset

**Solution:**
```bash
# Check volumes
docker volume ls | grep invoice

# Don't use -v flag when stopping
docker-compose down  # Good
docker-compose down -v  # Bad - deletes volumes

# Restore from backup
docker-compose exec -T db psql -U invoice_user invoice_app < backup.sql
```

---

## Getting More Help

### Collect Diagnostic Information

```bash
# System info
docker --version
docker-compose --version
uname -a

# Service status
docker-compose ps

# Recent logs
docker-compose logs --tail=100 > logs.txt

# Environment (sanitized)
cat .env | sed 's/=.*/=***/' > env-sanitized.txt
```

### Enable Debug Mode

```bash
# In .env
FLASK_ENV=development
FLASK_DEBUG=1

# Restart
docker-compose restart web

# Check logs
docker-compose logs -f web
```

### Access Python Shell

```bash
docker-compose exec web flask shell

# Test components
>>> from app.models import User, Batch
>>> User.query.all()
>>> Batch.query.all()
```

---

## Prevention

### Regular Maintenance

```bash
# Weekly
docker-compose logs --tail=1000 > logs/weekly-$(date +%Y%m%d).log
docker system df  # Check disk usage

# Monthly
docker system prune  # Clean up
# Backup database
docker-compose exec db pg_dump -U invoice_user invoice_app > backup-$(date +%Y%m%d).sql
```

### Monitoring

```bash
# Watch logs
docker-compose logs -f

# Monitor resources
docker stats

# Check health
./verify.sh
```

---

## Still Stuck?

1. **Check FAQ.md** for common questions
2. **Review logs** carefully for error messages
3. **Run verification** script: `./verify.sh`
4. **Check documentation** for specific features
5. **Open an issue** with diagnostic information

---

*Last Updated: 2026-02-03*
*Version: 1.0.0*
