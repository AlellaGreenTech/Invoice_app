# Backup and Restore Guide

Complete guide for backing up and restoring Invoice Processor data.

---

## Overview

Regular backups are essential for:
- Disaster recovery
- Data migration
- Testing and development
- Compliance requirements

---

## What to Backup

### Critical Data

1. **Database** (PostgreSQL)
   - User accounts
   - Batches
   - Invoices
   - Categories

2. **Configuration**
   - `.env` file (without sensitive data)
   - Custom configurations

3. **Logs** (optional)
   - Application logs
   - Error logs

### Not Needed

- Docker images (can be rebuilt)
- Temporary files
- Cache data
- PDF files (stored in Google Drive)

---

## Database Backup

### Manual Backup

#### Full Database Backup

```bash
# Backup entire database
docker-compose exec db pg_dump -U invoice_user invoice_app > backup-$(date +%Y%m%d-%H%M%S).sql

# Backup with compression
docker-compose exec db pg_dump -U invoice_user invoice_app | gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz
```

#### Backup Specific Tables

```bash
# Backup only users table
docker-compose exec db pg_dump -U invoice_user -t users invoice_app > users-backup.sql

# Backup multiple tables
docker-compose exec db pg_dump -U invoice_user -t users -t batches invoice_app > partial-backup.sql
```

#### Custom Format Backup (Recommended)

```bash
# Custom format (allows selective restore)
docker-compose exec db pg_dump -U invoice_user -Fc invoice_app > backup-$(date +%Y%m%d).dump
```

### Automated Backup

#### Daily Backup Script

Create `backup.sh`:

```bash
#!/bin/bash
# backup.sh - Automated database backup

BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d-%H%M%S)
FILENAME="invoice_app_backup_${DATE}.sql.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Perform backup
docker-compose exec -T db pg_dump -U invoice_user invoice_app | gzip > "${BACKUP_DIR}/${FILENAME}"

# Keep only last 30 days of backups
find "$BACKUP_DIR" -name "invoice_app_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${FILENAME}"
```

Make it executable:
```bash
chmod +x backup.sh
```

#### Schedule with Cron

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * /path/to/invoice_app/backup.sh >> /path/to/logs/backup.log 2>&1

# Add weekly backup on Sunday at 3 AM
0 3 * * 0 /path/to/invoice_app/backup.sh >> /path/to/logs/backup.log 2>&1
```

---

## Database Restore

### Full Database Restore

#### From SQL File

```bash
# Stop application
docker-compose down

# Start only database
docker-compose up -d db

# Wait for database to be ready
sleep 5

# Restore database
docker-compose exec -T db psql -U invoice_user invoice_app < backup.sql

# Or from compressed backup
gunzip -c backup.sql.gz | docker-compose exec -T db psql -U invoice_user invoice_app

# Start all services
docker-compose up -d
```

#### From Custom Format

```bash
# Restore from custom format
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app backup.dump

# Restore with clean (drop existing objects first)
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -c backup.dump
```

### Selective Restore

#### Restore Specific Tables

```bash
# Restore only users table
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -t users backup.dump

# Restore multiple tables
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -t users -t batches backup.dump
```

#### Restore Specific Data

```bash
# Restore only data (no schema)
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -a backup.dump

# Restore only schema (no data)
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -s backup.dump
```

---

## Configuration Backup

### Backup Configuration Files

```bash
# Create config backup directory
mkdir -p backups/config

# Backup .env (sanitized)
cat .env | sed 's/=.*/=***/' > backups/config/env-template.txt

# Backup docker-compose.yml
cp docker-compose.yml backups/config/

# Backup custom configurations
cp -r app/config.py backups/config/
```

### Restore Configuration

```bash
# Restore docker-compose.yml
cp backups/config/docker-compose.yml .

# Restore and update .env
cp backups/config/env-template.txt .env
# Edit .env to add actual values
nano .env
```

---

## Complete System Backup

### Full Backup Script

Create `full-backup.sh`:

```bash
#!/bin/bash
# full-backup.sh - Complete system backup

BACKUP_ROOT="/path/to/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${DATE}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting full backup: ${DATE}"

# 1. Backup database
echo "Backing up database..."
docker-compose exec -T db pg_dump -U invoice_user -Fc invoice_app > "${BACKUP_DIR}/database.dump"

# 2. Backup configuration (sanitized)
echo "Backing up configuration..."
cat .env | sed 's/=.*/=***/' > "${BACKUP_DIR}/env-template.txt"
cp docker-compose.yml "${BACKUP_DIR}/"
cp requirements.txt "${BACKUP_DIR}/"

# 3. Backup logs (last 7 days)
echo "Backing up logs..."
docker-compose logs --since 7d > "${BACKUP_DIR}/logs.txt"

# 4. Create backup manifest
echo "Creating manifest..."
cat > "${BACKUP_DIR}/manifest.txt" << EOF
Backup Date: ${DATE}
Database: Yes
Configuration: Yes
Logs: Yes (7 days)
Application Version: $(cat VERSION 2>/dev/null || echo "1.0.0")
EOF

# 5. Compress backup
echo "Compressing backup..."
cd "$BACKUP_ROOT"
tar -czf "${DATE}.tar.gz" "${DATE}"
rm -rf "${DATE}"

# 6. Cleanup old backups (keep last 30 days)
find "$BACKUP_ROOT" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${DATE}.tar.gz"
echo "Location: ${BACKUP_ROOT}/${DATE}.tar.gz"
```

### Full Restore Script

Create `full-restore.sh`:

```bash
#!/bin/bash
# full-restore.sh - Complete system restore

if [ -z "$1" ]; then
    echo "Usage: ./full-restore.sh <backup-file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"
RESTORE_DIR="restore-$(date +%Y%m%d-%H%M%S)"

echo "Starting restore from: ${BACKUP_FILE}"

# 1. Extract backup
echo "Extracting backup..."
mkdir -p "$RESTORE_DIR"
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR" --strip-components=1

# 2. Stop application
echo "Stopping application..."
docker-compose down

# 3. Restore database
echo "Restoring database..."
docker-compose up -d db
sleep 5
docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -c "${RESTORE_DIR}/database.dump"

# 4. Restore configuration
echo "Restoring configuration..."
echo "Please update .env with actual values from: ${RESTORE_DIR}/env-template.txt"

# 5. Start application
echo "Starting application..."
docker-compose up -d

echo "Restore completed!"
echo "Don't forget to update .env with actual credentials"
```

---

## Backup Strategies

### Development

- **Frequency**: Before major changes
- **Retention**: 7 days
- **Method**: Manual backups
- **Storage**: Local disk

### Production

- **Frequency**: Daily (automated)
- **Retention**: 30 days (daily), 12 months (monthly)
- **Method**: Automated with monitoring
- **Storage**: Off-site (S3, Cloud Storage)

---

## Cloud Backup

### AWS S3

```bash
# Install AWS CLI
pip install awscli

# Configure AWS
aws configure

# Backup to S3
docker-compose exec -T db pg_dump -U invoice_user -Fc invoice_app | \
  aws s3 cp - s3://your-bucket/backups/invoice_app_$(date +%Y%m%d).dump

# Restore from S3
aws s3 cp s3://your-bucket/backups/invoice_app_20240115.dump - | \
  docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -c
```

### Google Cloud Storage

```bash
# Install gsutil
pip install gsutil

# Backup to GCS
docker-compose exec -T db pg_dump -U invoice_user -Fc invoice_app | \
  gsutil cp - gs://your-bucket/backups/invoice_app_$(date +%Y%m%d).dump

# Restore from GCS
gsutil cp gs://your-bucket/backups/invoice_app_20240115.dump - | \
  docker-compose exec -T db pg_restore -U invoice_user -d invoice_app -c
```

---

## Backup Verification

### Test Restore

Regularly test your backups:

```bash
# 1. Create test environment
docker-compose -f docker-compose.test.yml up -d

# 2. Restore backup to test environment
docker-compose -f docker-compose.test.yml exec -T db pg_restore -U invoice_user -d invoice_app backup.dump

# 3. Verify data
docker-compose -f docker-compose.test.yml exec db psql -U invoice_user -d invoice_app -c "SELECT count(*) FROM users;"

# 4. Cleanup
docker-compose -f docker-compose.test.yml down -v
```

### Backup Integrity Check

```bash
# Check SQL file
gunzip -t backup.sql.gz

# Check custom format
docker-compose exec -T db pg_restore -l backup.dump
```

---

## Disaster Recovery

### Recovery Time Objective (RTO)

Target time to restore service: **< 1 hour**

### Recovery Point Objective (RPO)

Maximum acceptable data loss: **< 24 hours**

### Recovery Steps

1. **Assess Situation**
   - Identify what failed
   - Determine data loss extent
   - Check backup availability

2. **Prepare Environment**
   ```bash
   # Pull latest code
   git pull origin main

   # Rebuild containers
   docker-compose build
   ```

3. **Restore Database**
   ```bash
   # Restore from latest backup
   ./full-restore.sh backups/latest.tar.gz
   ```

4. **Verify System**
   ```bash
   # Run verification
   ./verify.sh

   # Check services
   docker-compose ps

   # Test functionality
   curl http://localhost:5000/health
   ```

5. **Resume Operations**
   ```bash
   # Start all services
   docker-compose up -d

   # Monitor logs
   docker-compose logs -f
   ```

---

## Backup Checklist

### Daily
- [ ] Automated database backup runs
- [ ] Backup completes successfully
- [ ] Backup file size is reasonable
- [ ] Old backups are cleaned up

### Weekly
- [ ] Test restore from backup
- [ ] Verify backup integrity
- [ ] Check backup storage space
- [ ] Review backup logs

### Monthly
- [ ] Full system backup
- [ ] Off-site backup copy
- [ ] Disaster recovery test
- [ ] Update backup procedures

---

## Backup Best Practices

1. **3-2-1 Rule**
   - 3 copies of data
   - 2 different media types
   - 1 off-site copy

2. **Encryption**
   ```bash
   # Encrypt backup
   docker-compose exec -T db pg_dump -U invoice_user invoice_app | \
     gpg --encrypt --recipient your@email.com > backup.sql.gpg

   # Decrypt backup
   gpg --decrypt backup.sql.gpg | \
     docker-compose exec -T db psql -U invoice_user invoice_app
   ```

3. **Automation**
   - Use cron for scheduling
   - Monitor backup jobs
   - Alert on failures

4. **Documentation**
   - Document backup procedures
   - Keep restore instructions updated
   - Test regularly

5. **Security**
   - Encrypt backups
   - Secure backup storage
   - Limit access to backups
   - Sanitize sensitive data

---

## Troubleshooting

### Backup Fails

```bash
# Check disk space
df -h

# Check database connection
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT 1;"

# Check permissions
ls -la backups/
```

### Restore Fails

```bash
# Check backup file
file backup.sql.gz

# Check database is running
docker-compose ps db

# Check for conflicts
docker-compose exec db psql -U invoice_user -d invoice_app -c "\dt"
```

### Corrupted Backup

```bash
# Verify backup integrity
gunzip -t backup.sql.gz

# Try previous backup
ls -lt backups/

# Check backup logs
cat logs/backup.log
```

---

*Last Updated: 2026-02-03*
*Version: 1.0.0*
