# Deployment & Production Checklist

## ✅ Pre-Deployment Verification

### Code Quality

- [ ] All endpoints tested
- [ ] Error handling in place
- [ ] Input validation working
- [ ] CORS configured correctly
- [ ] Database migrations tested
- [ ] File permissions set correctly
- [ ] Secrets not hardcoded

### Testing

- [ ] Unit tests passing (if added)
- [ ] Integration tests passing
- [ ] API endpoint tests complete
- [ ] File upload/processing tested
- [ ] Database operations tested
- [ ] Error scenarios handled

### Documentation

- [ ] README.md updated
- [ ] API_ENDPOINTS.md complete
- [ ] Code comments added
- [ ] Deployment instructions written
- [ ] Environment variables documented

### Security

- [ ] No credentials in code
- [ ] .env.example updated
- [ ] Dependencies up to date
- [ ] SQL injection prevented (SQLAlchemy ORM)
- [ ] CORS properly configured

---

## 🐳 Deployment Option 1: Docker

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app ./app
COPY .env.example .env

# Create directories
RUN mkdir -p uploads pages lines

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Create docker-compose.yml

```yaml
version: "3.8"

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./pages:/app/pages
      - ./lines:/app/lines
      - ./test.db:/app/test.db
    environment:
      - DATABASE_URL=sqlite:///./test.db
      - DEBUG=False
    restart: unless-stopped

  postgres: # Optional: for production database
    image: postgres:15
    environment:
      POSTGRES_DB: train_printed
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Build and Run

```bash
docker-compose build
docker-compose up -d
```

---

## ☁️ Deployment Option 2: Cloud (Heroku/Railway/Render)

### Heroku Deployment

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set environment variables
heroku config:set DATABASE_URL=postgresql://...

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### Procfile

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Railway/Render

1. Connect GitHub repository
2. Set environment variables
3. Set start command: `uvicorn app.main:app --host 0.0.0.0`
4. Deploy!

---

## 📊 Production Configuration

### Update .env for Production

```
DATABASE_URL=postgresql://user:password@prod-db:5432/train_printed
DEBUG=False
API_PORT=8000
MAX_UPLOAD_SIZE=100000000
JWT_SECRET_KEY=your-very-secret-key
```

### Production Dependencies

```bash
pip install gunicorn
pip install psycopg2-binary  # PostgreSQL driver
```

### Run with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

---

## 🗄️ Database Migration

### From SQLite to PostgreSQL

```python
# Step 1: Export SQLite data
# Step 2: Create PostgreSQL database
# Step 3: Update SQLALCHEMY_DATABASE_URL
SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@localhost/train_printed"
# Step 4: Run migration script
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

---

## 🔐 Security Hardening

### 1. Add Authentication

```python
# app/auth.py
from fastapi_jwt_extended import JWTManager, create_access_token
from fastapi import Depends, HTTPException

jwt = JWTManager()

@app.post("/auth/login")
def login(email: str, password: str):
    # Verify credentials
    access_token = create_access_token(identity=user_id)
    return {"access_token": access_token}

def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify and decode token
    return user
```

### 2. Add Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/documents")
@limiter.limit("100/minute")
def list_documents(request: Request):
    # ...
```

### 3. Add HTTPS

- Use proper SSL certificates
- Redirect HTTP to HTTPS
- Set secure cookie flags

### 4. Input Validation

- All endpoints already use Pydantic
- Add file type validation
- Add size limits

---

## 📈 Monitoring & Logging

### Add Structured Logging

```python
# app/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('app.log', maxBytes=10485760, backupCount=10),
        logging.StreamHandler()
    ]
)
```

### Add Error Tracking (Sentry)

```bash
pip install sentry-sdk

# In main.py
import sentry_sdk
sentry_sdk.init(
    dsn="your-sentry-dsn",
    traces_sample_rate=0.1
)
```

### Add Performance Monitoring

```python
# Add prometheus metrics
pip install prometheus-fastapi-instrumentator

from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

---

## 🧹 Cleanup & Maintenance

### Database Cleanup

```python
# app/maintenance.py
from datetime import datetime, timedelta

def cleanup_old_uploads():
    """Delete uploads older than 30 days"""
    cutoff = datetime.now() - timedelta(days=30)
    old_documents = db.query(Document).filter(
        Document.created_at < cutoff,
        Document.status == "failed"
    ).all()

    for doc in old_documents:
        # Delete files and database record
        pass

# Schedule with APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(cleanup_old_uploads, 'cron', hour=2, minute=0)
scheduler.start()
```

### Backup Strategy

```bash
# Daily database backup
0 2 * * * pg_dump train_printed > /backups/backup_$(date +\%Y\%m\%d).sql

# Backup uploads directory
0 3 * * * tar -czf /backups/uploads_$(date +\%Y\%m\%d).tar.gz /app/uploads/
```

---

## 🚨 Troubleshooting Production Issues

### API not responding

```bash
# Check logs
docker logs <container_id>

# Check port
netstat -tlnp | grep 8000

# Restart
docker-compose restart api
```

### Database connection issues

```bash
# Test connection
psql postgresql://user:pass@host/db

# Check credentials
echo $DATABASE_URL
```

### File permission errors

```bash
# Fix directory permissions
chmod 755 uploads pages lines

# Fix file permissions
chmod 644 uploads/*
```

### Out of disk space

```bash
# Check disk usage
df -h

# Clean old uploads
rm -rf uploads/*_old/
```

---

## 📋 Pre-Launch Checklist

### Infrastructure

- [ ] Server provisioned
- [ ] Domain configured
- [ ] SSL certificate installed
- [ ] Database created
- [ ] Storage directories created
- [ ] Backups configured

### Application

- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Static files served correctly
- [ ] API endpoints tested
- [ ] Health check working
- [ ] Logging configured

### Documentation

- [ ] Deployment documented
- [ ] Runbooks created
- [ ] Monitoring configured
- [ ] Alert thresholds set
- [ ] Contact information updated

### Testing

- [ ] Load testing completed
- [ ] Error scenarios tested
- [ ] Security audit passed
- [ ] Performance acceptable
- [ ] Failover tested

---

## 📞 Support & Monitoring

### Health Check Endpoint

```bash
# Monitor with:
curl http://localhost:8000/health
```

### Key Metrics to Monitor

- API response time
- Database query time
- Error rates
- File upload success rate
- Disk usage
- Memory usage
- CPU usage

### Set up Alerts for

- API down (no response)
- Error rate > 5%
- Response time > 1s
- Disk usage > 80%
- Database connection errors

---

## 🔄 CI/CD Setup (GitHub Actions)

### .github/workflows/deploy.yml

```yaml
name: Deploy API

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pytest

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          # Your deployment script
          docker-compose up -d
```

---

## 📚 Useful Commands

```bash
# View logs
tail -f app.log

# Count line images
find lines -name "*.tif" | wc -l

# Check API status
curl -X GET http://localhost:8000/health

# Database backup
pg_dump train_printed > backup.sql

# Restore database
psql train_printed < backup.sql

# Clean old files
find uploads -mtime +30 -delete
```

---

## ✅ Launch Checklist

- [ ] All code tested
- [ ] Documentation complete
- [ ] Security hardened
- [ ] Database optimized
- [ ] Monitoring active
- [ ] Backups running
- [ ] Team trained
- [ ] Support plan ready

**Ready to launch! 🚀**
