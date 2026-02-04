# Quick Command Reference

Essential commands for Invoice Processor.

---

## 🚀 Getting Started

```bash
# Initial setup
./setup.sh

# Or manually
docker-compose up --build -d
docker-compose exec web flask db upgrade
docker-compose exec web flask seed-categories
```

---

## 🐳 Docker Commands

### Start/Stop
```bash
docker-compose up -d              # Start all services
docker-compose down               # Stop all services
docker-compose restart            # Restart all services
docker-compose restart web        # Restart specific service
```

### Status & Logs
```bash
docker-compose ps                 # Show service status
docker-compose logs -f            # Follow all logs
docker-compose logs -f web        # Follow web logs
docker-compose logs --tail=100    # Last 100 lines
```

### Maintenance
```bash
docker-compose build              # Rebuild containers
docker-compose pull               # Pull latest images
docker system prune               # Clean up Docker
docker volume prune               # Clean up volumes
```

---

## 🗄️ Database Commands

### Migrations
```bash
docker-compose exec web flask db upgrade        # Run migrations
docker-compose exec web flask db migrate -m "msg"  # Create migration
docker-compose exec web flask db downgrade      # Rollback migration
```

### Access Database
```bash
docker-compose exec db psql -U invoice_user -d invoice_app
```

### Common Queries
```sql
-- Count users
SELECT count(*) FROM users;

-- Count batches
SELECT count(*) FROM batches;

-- Recent batches
SELECT id, status, created_at FROM batches ORDER BY created_at DESC LIMIT 10;

-- Invoices by category
SELECT category, count(*) FROM invoices GROUP BY category;
```

### Backup & Restore
```bash
# Backup
docker-compose exec db pg_dump -U invoice_user invoice_app > backup.sql

# Restore
docker-compose exec -T db psql -U invoice_user invoice_app < backup.sql
```

---

## 🧪 Testing Commands

```bash
docker-compose exec web pytest                    # Run all tests
docker-compose exec web pytest -v                 # Verbose output
docker-compose exec web pytest --cov=app tests/   # With coverage
docker-compose exec web pytest tests/test_models.py  # Specific file
```

---

## 🔧 Flask Commands

### Shell Access
```bash
docker-compose exec web flask shell
```

### Custom Commands
```bash
docker-compose exec web flask seed-categories     # Seed categories
docker-compose exec web flask init-db            # Initialize DB
docker-compose exec web flask reset-db           # Reset DB (careful!)
```

---

## 📊 Monitoring Commands

### Resource Usage
```bash
docker stats                      # Real-time stats
docker stats --no-stream          # One-time snapshot
```

### Health Checks
```bash
curl http://localhost:5000/health                 # App health
docker-compose exec redis redis-cli ping          # Redis health
docker-compose exec db pg_isready -U invoice_user # DB health
```

### Celery
```bash
docker-compose exec celery celery -A celery_worker.celery status
docker-compose exec celery celery -A celery_worker.celery inspect active
docker-compose exec redis redis-cli llen celery   # Queue length
```

---

## 🔍 Debugging Commands

### View Logs
```bash
docker-compose logs -f web        # Web logs
docker-compose logs -f celery     # Celery logs
docker-compose logs | grep ERROR  # Filter errors
```

### Access Container
```bash
docker-compose exec web bash      # Web container shell
docker-compose exec db bash       # Database container shell
```

### Check Environment
```bash
docker-compose exec web env | grep GOOGLE    # Check env vars
cat .env                                     # View .env file
```

---

## 🛠️ Makefile Commands

```bash
make help         # Show all commands
make setup        # Complete setup
make up           # Start services
make down         # Stop services
make logs         # View logs
make test         # Run tests
make shell        # Flask shell
make migrate      # Run migrations
make seed         # Seed categories
make clean        # Clean up Docker
```

---

## 📦 Maintenance Commands

### Update Dependencies
```bash
# Update requirements.txt
pip install --upgrade -r requirements.txt

# Rebuild containers
docker-compose build
docker-compose up -d
```

### Clean Up
```bash
# Remove old containers
docker-compose down

# Remove volumes (careful - deletes data!)
docker-compose down -v

# Clean Docker system
docker system prune -a
```

### Backup
```bash
# Database backup
docker-compose exec db pg_dump -U invoice_user invoice_app > backup-$(date +%Y%m%d).sql

# Full backup
./backup.sh  # If you created the backup script
```

---

## 🔐 Security Commands

### Rotate Secret Key
```bash
# Generate new key
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Update .env
nano .env

# Restart
docker-compose restart web
```

### Check Permissions
```bash
ls -la .env                       # Check .env permissions
docker-compose exec web ls -la    # Check container permissions
```

---

## 📈 Performance Commands

### Database Performance
```sql
-- Slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC LIMIT 10;

-- Table sizes
SELECT tablename, pg_size_pretty(pg_total_relation_size(tablename::text))
FROM pg_tables WHERE schemaname = 'public';

-- Active connections
SELECT count(*) FROM pg_stat_activity;
```

### Optimize Database
```bash
docker-compose exec db psql -U invoice_user -d invoice_app -c "VACUUM ANALYZE;"
```

---

## 🚨 Emergency Commands

### Service Not Responding
```bash
docker-compose restart web
docker-compose logs -f web
```

### Database Issues
```bash
docker-compose restart db
docker-compose exec db pg_isready -U invoice_user
```

### Celery Not Processing
```bash
docker-compose restart celery
docker-compose restart redis
docker-compose logs -f celery
```

### Complete Reset (Nuclear Option)
```bash
docker-compose down -v
docker system prune -a
./setup.sh
```

---

## 📝 Common Workflows

### Process Invoices
1. Open http://localhost:5000
2. Login with Google
3. Click "Upload Invoices"
4. Paste Google Drive URL
5. Click "Start Processing"
6. Monitor progress
7. View summary
8. Export results

### Add New User
1. User visits http://localhost:5000
2. Clicks "Sign in with Google"
3. Authorizes application
4. Automatically created in database

### Update Category
1. Go to batch details
2. Click edit icon next to invoice
3. Enter new category
4. Changes saved automatically

### Export Data
```bash
# CSV export
curl http://localhost:5000/export/csv/1 > invoices.csv

# Or use web interface
# Go to batch summary → Click "Export CSV"
```

---

## 🔄 Update Workflow

### Update Application
```bash
git pull origin main
docker-compose build
docker-compose up -d
docker-compose exec web flask db upgrade
```

### Update Dependencies
```bash
# Edit requirements.txt
nano requirements.txt

# Rebuild
docker-compose build
docker-compose up -d
```

---

## 📞 Help Commands

```bash
./verify.sh                       # Run verification
docker-compose --help             # Docker Compose help
flask --help                      # Flask help
make help                         # Makefile help
```

---

## 💡 Pro Tips

```bash
# Tail logs from multiple services
docker-compose logs -f web celery

# Save logs to file
docker-compose logs > logs/app-$(date +%Y%m%d).log

# Watch resource usage
watch docker stats

# Monitor queue length
watch 'docker-compose exec redis redis-cli llen celery'

# Quick health check
curl -s http://localhost:5000/health | jq

# Database size
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT pg_size_pretty(pg_database_size('invoice_app'));"
```

---

## 🎯 Keyboard Shortcuts

### In Flask Shell
```python
# Import models
from app.models import User, Batch, Invoice

# Query examples
User.query.all()
Batch.query.filter_by(status='completed').all()
Invoice.query.count()

# Database session
from app.extensions import db
db.session.commit()
```

---

## 📚 More Information

- Full documentation: See all .md files in root
- Troubleshooting: TROUBLESHOOTING.md
- FAQ: FAQ.md
- API Reference: API.md

---

*Quick Reference v1.0.0*
*Last Updated: 2026-02-03*
