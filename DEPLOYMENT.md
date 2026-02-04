# Deployment Guide

This guide covers deploying the Invoice Processor application to various platforms.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Platform-Specific Guides](#platform-specific-guides)
4. [Database Setup](#database-setup)
5. [Security Checklist](#security-checklist)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before deploying, ensure you have:

- [ ] Google OAuth credentials configured
- [ ] Anthropic API key
- [ ] Production database (PostgreSQL)
- [ ] Production Redis instance
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (for HTTPS)

## Environment Configuration

### Production Environment Variables

Create a `.env.production` file:

```bash
# Flask
FLASK_ENV=production
SECRET_KEY=<generate-secure-key>
DATABASE_URL=<production-database-url>
REDIS_URL=<production-redis-url>

# Google OAuth
GOOGLE_CLIENT_ID=<your-client-id>
GOOGLE_CLIENT_SECRET=<your-client-secret>
GOOGLE_REDIRECT_URI=https://yourdomain.com/auth/callback

# Anthropic Claude
ANTHROPIC_API_KEY=<your-api-key>

# Application Settings
MAX_CONTENT_LENGTH=104857600
UPLOAD_FOLDER=/tmp/invoices
```

### Generate Secure Secret Key

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

## Platform-Specific Guides

### Option 1: Render.com (Recommended for Beginners)

**Pros**: Free tier, easy setup, automatic HTTPS
**Cons**: Limited resources on free tier

#### Steps:

1. **Create Render Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create PostgreSQL Database**
   - Click "New +" → "PostgreSQL"
   - Name: `invoice-processor-db`
   - Plan: Free
   - Copy the Internal Database URL

3. **Create Redis Instance**
   - Click "New +" → "Redis"
   - Name: `invoice-processor-redis`
   - Plan: Free
   - Copy the Internal Redis URL

4. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Name: `invoice-processor`
   - Environment: Docker
   - Plan: Free
   - Add environment variables from `.env.production`

5. **Create Worker Service**
   - Click "New +" → "Background Worker"
   - Connect same repository
   - Name: `invoice-processor-worker`
   - Start Command: `celery -A celery_worker.celery worker --loglevel=info`
   - Add same environment variables

6. **Update Google OAuth**
   - Go to Google Cloud Console
   - Update redirect URI: `https://your-app.onrender.com/auth/callback`

7. **Deploy**
   - Render will automatically deploy
   - Run migrations via Render Shell:
     ```bash
     flask db upgrade
     flask seed-categories
     ```

### Option 2: Railway.app

**Pros**: $5/month credit, easy deployment, good performance
**Cons**: Requires credit card

#### Steps:

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add PostgreSQL**
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will provide DATABASE_URL

4. **Add Redis**
   - Click "New" → "Database" → "Redis"
   - Railway will provide REDIS_URL

5. **Configure Environment Variables**
   - Click on your service
   - Go to "Variables"
   - Add all production variables

6. **Configure Services**
   - Web service: Uses Dockerfile automatically
   - Add worker service:
     - Click "New" → "Empty Service"
     - Same repo, different start command
     - Command: `celery -A celery_worker.celery worker --loglevel=info`

7. **Deploy**
   - Railway deploys automatically
   - Access shell to run migrations

### Option 3: Heroku

**Pros**: Mature platform, good documentation
**Cons**: No free tier anymore

#### Steps:

1. **Install Heroku CLI**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Login**
   ```bash
   heroku login
   ```

3. **Create App**
   ```bash
   heroku create invoice-processor
   ```

4. **Add Buildpacks**
   ```bash
   heroku buildpacks:set heroku/python
   ```

5. **Add Add-ons**
   ```bash
   heroku addons:create heroku-postgresql:mini
   heroku addons:create heroku-redis:mini
   ```

6. **Set Environment Variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set SECRET_KEY=<your-secret-key>
   heroku config:set GOOGLE_CLIENT_ID=<your-client-id>
   heroku config:set GOOGLE_CLIENT_SECRET=<your-client-secret>
   heroku config:set ANTHROPIC_API_KEY=<your-api-key>
   ```

7. **Create Procfile**
   ```
   web: gunicorn run:app
   worker: celery -A celery_worker.celery worker --loglevel=info
   ```

8. **Deploy**
   ```bash
   git push heroku main
   heroku run flask db upgrade
   heroku run flask seed-categories
   ```

9. **Scale Worker**
   ```bash
   heroku ps:scale worker=1
   ```

### Option 4: AWS (Advanced)

**Pros**: Full control, scalable, many services
**Cons**: Complex setup, requires AWS knowledge

#### Architecture:

- **ECS/Fargate**: Container orchestration
- **RDS PostgreSQL**: Managed database
- **ElastiCache Redis**: Managed Redis
- **ALB**: Load balancer
- **S3**: File storage (optional)
- **CloudWatch**: Logging and monitoring

#### Steps:

1. **Create RDS PostgreSQL**
   - Go to RDS console
   - Create database
   - Choose PostgreSQL 15
   - Note connection details

2. **Create ElastiCache Redis**
   - Go to ElastiCache console
   - Create Redis cluster
   - Note endpoint

3. **Build and Push Docker Image**
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name invoice-processor

   # Build image
   docker build -t invoice-processor .

   # Tag and push
   docker tag invoice-processor:latest <account-id>.dkr.ecr.<region>.amazonaws.com/invoice-processor:latest
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/invoice-processor:latest
   ```

4. **Create ECS Cluster**
   - Go to ECS console
   - Create cluster (Fargate)

5. **Create Task Definitions**
   - Web service task
   - Worker service task
   - Configure environment variables

6. **Create Services**
   - Web service with ALB
   - Worker service

7. **Configure ALB**
   - Create target group
   - Configure health checks
   - Add SSL certificate

8. **Update DNS**
   - Point domain to ALB

## Database Setup

### Run Migrations

```bash
# Render/Railway
# Use platform's shell feature

# Heroku
heroku run flask db upgrade

# AWS
aws ecs run-task --task-definition migration-task
```

### Seed Categories

```bash
flask seed-categories
```

### Backup Strategy

1. **Automated Backups**
   - Enable on your database platform
   - Retention: 7-30 days

2. **Manual Backups**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

3. **Restore**
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

## Security Checklist

### Before Deployment

- [ ] Change SECRET_KEY to production value
- [ ] Use HTTPS only
- [ ] Enable CSRF protection
- [ ] Set secure cookie flags
- [ ] Validate all environment variables
- [ ] Review OAuth scopes
- [ ] Enable rate limiting
- [ ] Set up firewall rules
- [ ] Encrypt sensitive data at rest
- [ ] Use environment variables for secrets
- [ ] Enable database SSL
- [ ] Set up VPC (if using AWS)

### Production Settings

```python
# config.py additions for production
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # HTTPS
    PREFERRED_URL_SCHEME = 'https'

    # Rate limiting
    RATELIMIT_ENABLED = True
```

### Update OAuth Redirect URI

In Google Cloud Console:
- Update redirect URI to production domain
- Example: `https://yourdomain.com/auth/callback`

## Monitoring

### Application Monitoring

1. **Logging**
   ```python
   import logging

   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s %(levelname)s: %(message)s'
   )
   ```

2. **Error Tracking**
   - Sentry (recommended)
   - Rollbar
   - Bugsnag

3. **Performance Monitoring**
   - New Relic
   - DataDog
   - Application Insights

### Health Checks

Add health check endpoint:

```python
@app.route('/health')
def health():
    return {'status': 'healthy'}, 200
```

### Metrics to Monitor

- Request rate
- Response time
- Error rate
- Database connections
- Celery queue length
- Memory usage
- CPU usage

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

#### Celery Worker Not Processing

```bash
# Check worker logs
# Render: View logs in dashboard
# Heroku: heroku logs --tail --dyno worker

# Verify Redis connection
redis-cli -u $REDIS_URL ping
```

#### OAuth Errors

- Verify redirect URI matches exactly
- Check client ID and secret
- Ensure APIs are enabled in Google Console

#### Static Files Not Loading

```bash
# Collect static files
flask collect-static

# Or use CDN for production
```

### Performance Optimization

1. **Database**
   - Add indexes
   - Use connection pooling
   - Enable query caching

2. **Redis**
   - Use for session storage
   - Cache frequently accessed data

3. **Application**
   - Enable gzip compression
   - Use CDN for static files
   - Optimize images

4. **Celery**
   - Scale workers based on load
   - Use task priorities
   - Set task timeouts

## Post-Deployment

### Verify Deployment

- [ ] Application loads
- [ ] Can log in with Google
- [ ] Can upload and process invoices
- [ ] Can export to CSV
- [ ] Can export to Google Sheets
- [ ] Background processing works
- [ ] Error pages display correctly

### Set Up Monitoring

- [ ] Configure error tracking
- [ ] Set up uptime monitoring
- [ ] Configure alerts
- [ ] Set up log aggregation

### Documentation

- [ ] Document deployment process
- [ ] Create runbook for common issues
- [ ] Document rollback procedure
- [ ] Create incident response plan

## Scaling

### Horizontal Scaling

- Add more web workers
- Add more Celery workers
- Use load balancer

### Vertical Scaling

- Increase instance size
- Increase database resources
- Increase Redis memory

### Database Scaling

- Read replicas
- Connection pooling
- Query optimization

## Maintenance

### Regular Tasks

- Monitor error rates
- Review logs
- Check database size
- Update dependencies
- Rotate secrets
- Review access logs

### Updates

```bash
# Update dependencies
pip install -U -r requirements.txt

# Run migrations
flask db upgrade

# Restart services
# Platform-specific commands
```

## Rollback Procedure

1. **Identify issue**
2. **Revert to previous version**
   ```bash
   # Heroku
   heroku rollback

   # Render/Railway
   # Use dashboard to rollback
   ```
3. **Verify rollback**
4. **Investigate issue**
5. **Fix and redeploy**

---

**Need help?** Check the troubleshooting section or open an issue on GitHub.
