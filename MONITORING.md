# Monitoring Guide

Complete guide for monitoring the Invoice Processor application.

---

## Overview

Monitoring is essential for:
- Detecting issues early
- Understanding performance
- Planning capacity
- Debugging problems
- Ensuring uptime

---

## Health Checks

### Application Health

The application includes a health check endpoint:

```bash
# Check application health
curl http://localhost:5000/health

# Expected response
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": "1.0.0"
}
```

### Service Health

Check all services:

```bash
# Docker Compose
docker-compose ps

# Expected output: All services "Up"
```

### Database Health

```bash
# Check PostgreSQL
docker-compose exec db pg_isready -U invoice_user

# Check connections
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT count(*) FROM pg_stat_activity;"
```

### Redis Health

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Expected: PONG
```

### Celery Health

```bash
# Check Celery workers
docker-compose exec celery celery -A celery_worker.celery inspect active

# Check queue length
docker-compose exec redis redis-cli llen celery
```

---

## Metrics to Monitor

### Application Metrics

1. **Request Rate**
   - Requests per second
   - Requests per endpoint
   - Success vs error rate

2. **Response Time**
   - Average response time
   - 95th percentile
   - 99th percentile
   - Slowest endpoints

3. **Error Rate**
   - 4xx errors (client errors)
   - 5xx errors (server errors)
   - Error types and frequency

4. **User Activity**
   - Active users
   - Login attempts
   - Batch processing requests

### System Metrics

1. **CPU Usage**
   ```bash
   docker stats --no-stream
   ```

2. **Memory Usage**
   ```bash
   docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"
   ```

3. **Disk Usage**
   ```bash
   # Docker disk usage
   docker system df

   # Database size
   docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT pg_size_pretty(pg_database_size('invoice_app'));"
   ```

4. **Network I/O**
   ```bash
   docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"
   ```

### Database Metrics

1. **Connection Count**
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

2. **Query Performance**
   ```sql
   SELECT query, calls, total_time, mean_time
   FROM pg_stat_statements
   ORDER BY total_time DESC
   LIMIT 10;
   ```

3. **Table Sizes**
   ```sql
   SELECT
     schemaname,
     tablename,
     pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

4. **Slow Queries**
   ```sql
   SELECT
     query,
     calls,
     total_time,
     mean_time,
     max_time
   FROM pg_stat_statements
   WHERE mean_time > 1000  -- queries taking more than 1 second
   ORDER BY mean_time DESC;
   ```

### Celery Metrics

1. **Task Queue Length**
   ```bash
   docker-compose exec redis redis-cli llen celery
   ```

2. **Active Tasks**
   ```bash
   docker-compose exec celery celery -A celery_worker.celery inspect active
   ```

3. **Task Success/Failure Rate**
   ```bash
   docker-compose exec celery celery -A celery_worker.celery inspect stats
   ```

4. **Worker Status**
   ```bash
   docker-compose exec celery celery -A celery_worker.celery status
   ```

---

## Logging

### Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f celery

# Last N lines
docker-compose logs --tail=100

# Since timestamp
docker-compose logs --since 2024-01-01T00:00:00

# Filter by level
docker-compose logs | grep ERROR
```

### Log Analysis

```bash
# Count errors
docker-compose logs | grep ERROR | wc -l

# Most common errors
docker-compose logs | grep ERROR | sort | uniq -c | sort -rn | head -10

# Errors by service
docker-compose logs web | grep ERROR | wc -l
docker-compose logs celery | grep ERROR | wc -l
```

### Log Aggregation

For production, consider:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana Loki**
- **Datadog**
- **CloudWatch** (AWS)
- **Stackdriver** (GCP)

---

## Alerting

### Critical Alerts

Set up alerts for:

1. **Service Down**
   - Any service not responding
   - Health check failures

2. **High Error Rate**
   - More than 5% error rate
   - Sustained errors for 5+ minutes

3. **Database Issues**
   - Connection pool exhausted
   - Slow queries (>5 seconds)
   - Disk space low (<10%)

4. **Celery Issues**
   - Queue length >100
   - No active workers
   - Task failures >10%

5. **Resource Exhaustion**
   - CPU >80% for 5+ minutes
   - Memory >90%
   - Disk >90%

### Warning Alerts

Set up warnings for:

1. **Performance Degradation**
   - Response time >2 seconds
   - Queue length >50

2. **Resource Usage**
   - CPU >60%
   - Memory >70%
   - Disk >70%

3. **Unusual Activity**
   - Spike in failed logins
   - Unusual traffic patterns

---

## Monitoring Tools

### Built-in Tools

1. **Docker Stats**
   ```bash
   docker stats
   ```

2. **Verification Script**
   ```bash
   ./verify.sh
   ```

3. **Health Check**
   ```bash
   curl http://localhost:5000/health
   ```

### Recommended Tools

#### For Development

1. **Docker Desktop**
   - Built-in monitoring
   - Resource usage graphs

2. **pgAdmin** (PostgreSQL)
   ```bash
   docker run -p 5050:80 \
     -e PGADMIN_DEFAULT_EMAIL=admin@admin.com \
     -e PGADMIN_DEFAULT_PASSWORD=admin \
     dpage/pgadmin4
   ```

3. **Redis Commander**
   ```bash
   docker run -p 8081:8081 \
     -e REDIS_HOSTS=local:redis:6379 \
     rediscommander/redis-commander
   ```

#### For Production

1. **Prometheus + Grafana**
   - Metrics collection
   - Visualization
   - Alerting

2. **Sentry**
   - Error tracking
   - Performance monitoring
   - Release tracking

3. **Datadog**
   - Full-stack monitoring
   - APM
   - Log management

4. **New Relic**
   - Application monitoring
   - Infrastructure monitoring
   - Alerting

---

## Monitoring Checklist

### Daily

- [ ] Check service status
- [ ] Review error logs
- [ ] Check queue length
- [ ] Verify backups

### Weekly

- [ ] Review performance metrics
- [ ] Check disk usage
- [ ] Review slow queries
- [ ] Check for security updates

### Monthly

- [ ] Analyze trends
- [ ] Review capacity
- [ ] Update dependencies
- [ ] Test disaster recovery

---

## Dashboard Setup

### Simple Dashboard

Create a monitoring script:

```bash
#!/bin/bash
# monitor.sh

echo "=== Invoice Processor Status ==="
echo ""

echo "Services:"
docker-compose ps

echo ""
echo "Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

echo ""
echo "Queue Length:"
docker-compose exec redis redis-cli llen celery

echo ""
echo "Recent Errors:"
docker-compose logs --tail=50 | grep ERROR | tail -10
```

### Grafana Dashboard

For production, set up Grafana with:
- Request rate graph
- Response time graph
- Error rate graph
- Resource usage graphs
- Queue length graph

---

## Performance Baselines

### Expected Performance

- **Response Time**: <500ms for most requests
- **Batch Processing**: 1-2 seconds per invoice
- **Database Queries**: <100ms average
- **Memory Usage**: <2GB per service
- **CPU Usage**: <50% average

### When to Scale

Consider scaling when:
- Response time >2 seconds consistently
- CPU >80% for extended periods
- Memory >90%
- Queue length >100 consistently
- Error rate >5%

---

## Troubleshooting with Monitoring

### High CPU Usage

```bash
# Identify process
docker stats

# Check for runaway tasks
docker-compose logs celery | grep "Task"

# Check for slow queries
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

### High Memory Usage

```bash
# Check memory by service
docker stats --no-stream

# Check for memory leaks
docker-compose logs | grep "MemoryError"

# Restart service if needed
docker-compose restart web
```

### Slow Performance

```bash
# Check response times
docker-compose logs web | grep "response_time"

# Check database performance
docker-compose exec db psql -U invoice_user -d invoice_app -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check queue length
docker-compose exec redis redis-cli llen celery
```

---

## Monitoring Best Practices

1. **Set Baselines**
   - Establish normal metrics
   - Document expected values
   - Track trends over time

2. **Alert Fatigue**
   - Don't over-alert
   - Use appropriate thresholds
   - Group related alerts

3. **Regular Reviews**
   - Weekly metric reviews
   - Monthly trend analysis
   - Quarterly capacity planning

4. **Documentation**
   - Document alert responses
   - Keep runbooks updated
   - Track incidents

5. **Automation**
   - Automate health checks
   - Auto-restart failed services
   - Auto-scale when possible

---

*Last Updated: 2026-02-03*
*Version: 1.0.0*
