"""Flask extensions initialization."""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery

db = SQLAlchemy()
migrate = Migrate()

# Configure Celery with Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery = Celery(__name__, broker=redis_url, backend=redis_url)
