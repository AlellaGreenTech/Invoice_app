# Invoice Processor - File Index

Quick reference guide to all files in the project.

## 📁 Root Directory

| File | Purpose | Size |
|------|---------|------|
| `run.py` | Application entry point | 204B |
| `celery_worker.py` | Celery worker entry point | 186B |
| `requirements.txt` | Python dependencies | 555B |
| `Dockerfile` | Container definition | 603B |
| `docker-compose.yml` | Multi-container setup | 1.4K |
| `setup.sh` | Automated setup script | 2.8K |
| `pytest.ini` | Test configuration | 125B |
| `.env.example` | Environment template | 1.5K |
| `.env` | Environment variables | 1.5K |
| `.gitignore` | Git ignore rules | 485B |
| `.dockerignore` | Docker ignore rules | 300B |

## 📚 Documentation (9 files, 79K total)

| File | Purpose | Size |
|------|---------|------|
| `README.md` | Main documentation | 6.9K |
| `QUICKSTART.md` | 5-minute setup guide | 6.6K |
| `SETUP_COMPLETE.md` | Implementation details | 11K |
| `PROJECT_COMPLETE.md` | Project summary | 9.4K |
| `DEPLOYMENT.md` | Production deployment | 11K |
| `CONTRIBUTING.md` | Contribution guidelines | 8.7K |
| `CHANGELOG.md` | Version history | 6.4K |
| `STATISTICS.md` | Project metrics | 4.9K |
| `LICENSE` | MIT License | 1.1K |

## 🐍 Python Files (30 files, 3,200+ lines)

### Core Application (`app/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Flask app factory | 50 |
| `config.py` | Configuration classes | 80 |
| `models.py` | Database models | 130 |
| `routes.py` | Main routes | 30 |
| `errors.py` | Error handlers | 25 |
| `extensions.py` | Flask extensions | 10 |
| `cli.py` | CLI commands | 60 |

### Authentication (`app/auth/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Blueprint initialization | 5 |
| `routes.py` | OAuth routes | 108 |
| `google_auth.py` | Google OAuth helper | 161 |

### Invoice Processing (`app/invoices/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Blueprint initialization | 5 |
| `routes.py` | Invoice routes | 177 |
| `pdf_parser.py` | PDF extraction | 317 |
| `categorizer.py` | AI categorization | 250 |
| `drive_handler.py` | Google Drive ops | 246 |
| `tasks.py` | Celery background tasks | 213 |

### Export Functionality (`app/exports/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Blueprint initialization | 5 |
| `routes.py` | Export endpoints | 126 |
| `csv_exporter.py` | CSV generation | 140 |
| `sheets_uploader.py` | Google Sheets | 260 |

### Utilities (`app/utils/`)

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Package initialization | 1 |
| `validators.py` | Input validation | 80 |

## 🎨 Frontend Files

### Templates (`app/templates/`, 11 files)

| File | Purpose | Lines |
|------|---------|-------|
| `base.html` | Base template | 120 |
| `index.html` | Landing page | 150 |
| `dashboard.html` | User dashboard | 130 |
| `auth/login.html` | Login page | 40 |
| `invoices/upload.html` | Upload form | 120 |
| `invoices/processing.html` | Progress view | 140 |
| `invoices/summary.html` | Summary dashboard | 200 |
| `invoices/details.html` | Invoice list | 180 |
| `errors/403.html` | Forbidden error | 30 |
| `errors/404.html` | Not found error | 30 |
| `errors/500.html` | Server error | 30 |

### Static Files (`app/static/`)

| File | Purpose | Lines |
|------|---------|-------|
| `css/custom.css` | Custom styles | 150 |
| `js/app.js` | JavaScript utilities | 120 |

## 🧪 Test Files (`tests/`, 8 files)

| File | Purpose | Lines |
|------|---------|-------|
| `conftest.py` | Test fixtures | 80 |
| `test_models.py` | Model tests | 138 |
| `test_pdf_parser.py` | Parser tests | 115 |
| `test_categorizer.py` | Categorizer tests | 137 |
| `test_validators.py` | Validator tests | 100 |
| `test_csv_exporter.py` | Exporter tests | 119 |
| `test_routes.py` | Route tests | 60 |
| `__init__.py` | Package init | 1 |

## 📊 File Statistics

### By Type

- **Python files**: 30 (3,200+ lines)
- **HTML templates**: 11 (1,500+ lines)
- **JavaScript**: 1 (120 lines)
- **CSS**: 1 (150 lines)
- **Documentation**: 9 (79K)
- **Configuration**: 7 files
- **Total files**: 60+

### By Directory

```
app/
├── auth/           3 files (274 lines)
├── invoices/       6 files (1,208 lines)
├── exports/        4 files (531 lines)
├── static/         2 files (270 lines)
├── templates/      11 files (1,500 lines)
├── utils/          2 files (81 lines)
└── core/           7 files (385 lines)

tests/              8 files (750 lines)
docs/               9 files (79K)
config/             7 files
```

### Largest Files

1. `app/invoices/pdf_parser.py` - 317 lines
2. `app/exports/sheets_uploader.py` - 260 lines
3. `app/invoices/categorizer.py` - 250 lines
4. `app/invoices/drive_handler.py` - 246 lines
5. `app/invoices/tasks.py` - 213 lines

## 🔍 Quick File Lookup

### Need to modify...

**Authentication?**
- `app/auth/routes.py` - OAuth routes
- `app/auth/google_auth.py` - OAuth helper

**PDF Processing?**
- `app/invoices/pdf_parser.py` - Extraction logic
- `app/invoices/categorizer.py` - AI categorization

**Background Jobs?**
- `app/invoices/tasks.py` - Celery tasks
- `celery_worker.py` - Worker entry point

**Database?**
- `app/models.py` - Database models
- `app/config.py` - Database config

**UI/Templates?**
- `app/templates/` - All HTML templates
- `app/static/css/custom.css` - Styles
- `app/static/js/app.js` - JavaScript

**Export?**
- `app/exports/csv_exporter.py` - CSV export
- `app/exports/sheets_uploader.py` - Sheets export

**Tests?**
- `tests/test_*.py` - All test files
- `tests/conftest.py` - Test fixtures

**Configuration?**
- `.env` - Environment variables
- `app/config.py` - App configuration
- `docker-compose.yml` - Docker setup

**Documentation?**
- `README.md` - Main docs
- `QUICKSTART.md` - Setup guide
- `DEPLOYMENT.md` - Deploy guide

## 📝 File Naming Conventions

### Python Files
- `snake_case.py` for modules
- `PascalCase` for classes
- `snake_case` for functions

### Templates
- `lowercase.html` for templates
- Organized by feature in subdirectories

### Tests
- `test_*.py` for test files
- Match the module being tested

### Documentation
- `UPPERCASE.md` for main docs
- Descriptive names

## 🎯 Entry Points

### Application
- `run.py` - Start Flask app
- `celery_worker.py` - Start Celery worker

### CLI
- `flask db upgrade` - Run migrations
- `flask seed-categories` - Seed data
- `flask shell` - Python shell

### Docker
- `docker-compose up` - Start all services
- `docker-compose exec web bash` - Access container

### Tests
- `pytest` - Run all tests
- `pytest tests/test_models.py` - Run specific test

## 🔗 File Dependencies

### Core Dependencies
```
run.py
  └── app/__init__.py (app factory)
      ├── app/config.py
      ├── app/models.py
      ├── app/extensions.py
      ├── app/auth/
      ├── app/invoices/
      └── app/exports/
```

### Background Worker
```
celery_worker.py
  └── app/__init__.py
      └── app/invoices/tasks.py
          ├── app/invoices/pdf_parser.py
          ├── app/invoices/categorizer.py
          └── app/invoices/drive_handler.py
```

## 📦 Package Structure

```
invoice_app/
├── app/                    # Main application package
│   ├── auth/              # Authentication subpackage
│   ├── invoices/          # Invoice processing subpackage
│   ├── exports/           # Export functionality subpackage
│   ├── static/            # Static files
│   ├── templates/         # Jinja2 templates
│   └── utils/             # Utility functions
├── tests/                 # Test package
├── migrations/            # Database migrations (auto-generated)
└── docs/                  # Documentation (markdown files)
```

## 🚀 Most Important Files

If you're new to the project, start with these:

1. **README.md** - Overview and setup
2. **QUICKSTART.md** - Get started fast
3. **app/__init__.py** - App structure
4. **app/models.py** - Data models
5. **app/invoices/routes.py** - Main workflow
6. **docker-compose.yml** - Service setup
7. **.env.example** - Configuration template

---

**Total Project Size**: ~400KB
**Total Lines of Code**: ~5,000+
**Documentation**: 79KB across 9 files
**Test Coverage**: 8 comprehensive test files

---

*This index is current as of 2026-02-03*
