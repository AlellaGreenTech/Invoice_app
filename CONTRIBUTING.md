# Contributing to Invoice Processor

Thank you for your interest in contributing to the Invoice Processor! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Making Changes](#making-changes)
5. [Testing](#testing)
6. [Submitting Changes](#submitting-changes)
7. [Coding Standards](#coding-standards)
8. [Project Structure](#project-structure)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git
- Google Cloud Console account
- Anthropic API account

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/invoice_app.git
   cd invoice_app
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/invoice_app.git
   ```

## Development Setup

1. **Copy environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Configure credentials** in `.env`:
   - Google OAuth credentials
   - Anthropic API key
   - Secret key

3. **Start development environment**:
   ```bash
   docker-compose up --build
   ```

4. **Initialize database**:
   ```bash
   docker-compose exec web flask db upgrade
   docker-compose exec web flask seed-categories
   ```

5. **Run tests** to verify setup:
   ```bash
   docker-compose exec web pytest
   ```

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-multi-currency-support`
- `bugfix/fix-pdf-parsing-error`
- `docs/update-readme`
- `refactor/improve-categorizer`

### Commit Messages

Write clear, descriptive commit messages:

```
Add multi-currency conversion support

- Implement currency conversion API integration
- Add currency selection in UI
- Update database schema for currency rates
- Add tests for conversion logic

Closes #123
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description (wrap at 72 chars)
- Reference issues/PRs

### Development Workflow

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation

3. **Test your changes**:
   ```bash
   docker-compose exec web pytest
   docker-compose exec web pytest --cov=app tests/
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```

5. **Keep your branch updated**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

## Testing

### Running Tests

```bash
# Run all tests
docker-compose exec web pytest

# Run with coverage
docker-compose exec web pytest --cov=app tests/

# Run specific test file
docker-compose exec web pytest tests/test_pdf_parser.py

# Run with verbose output
docker-compose exec web pytest -v

# Run specific test
docker-compose exec web pytest tests/test_pdf_parser.py::TestPDFParser::test_extract_vendor_name
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use fixtures from `conftest.py`
- Test both success and failure cases
- Test edge cases

Example test:

```python
def test_extract_vendor_name(self):
    """Test vendor name extraction."""
    parser = PDFParser()
    text = "ACME Corporation\nInvoice #12345"
    vendor = parser.extract_vendor_name(text)
    assert vendor == "ACME Corporation"
```

### Test Coverage

Aim for:
- Overall coverage: 80%+
- New features: 90%+
- Critical paths: 100%

## Submitting Changes

### Pull Request Process

1. **Update documentation**:
   - Update README if needed
   - Add docstrings to new functions
   - Update CHANGELOG.md

2. **Ensure tests pass**:
   ```bash
   docker-compose exec web pytest
   ```

3. **Create pull request**:
   - Go to GitHub
   - Click "New Pull Request"
   - Select your branch
   - Fill in PR template

4. **PR Description should include**:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Screenshots (if UI changes)
   - Related issues

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Added new tests
- [ ] Updated existing tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
- [ ] CHANGELOG.md updated
```

## Coding Standards

### Python Style

Follow PEP 8 with these specifics:

- **Line length**: 100 characters max
- **Indentation**: 4 spaces
- **Imports**: Group by standard library, third-party, local
- **Docstrings**: Use Google style

Example:

```python
def process_invoice(invoice_data):
    """
    Process an invoice and extract data.

    Args:
        invoice_data: Dictionary containing invoice information

    Returns:
        dict: Processed invoice data with extracted fields

    Raises:
        ValueError: If invoice_data is invalid
    """
    if not invoice_data:
        raise ValueError("Invoice data is required")

    # Process invoice
    result = extract_fields(invoice_data)
    return result
```

### Code Organization

- **One class per file** (unless closely related)
- **Functions**: Keep under 50 lines
- **Classes**: Keep under 300 lines
- **Modules**: Keep under 500 lines

### Naming Conventions

- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Error Handling

```python
# Good
try:
    result = process_data(data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return None

# Bad
try:
    result = process_data(data)
except:
    pass
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

## Project Structure

```
invoice_app/
├── app/
│   ├── __init__.py          # App factory
│   ├── models.py            # Database models
│   ├── config.py            # Configuration
│   ├── auth/                # Authentication
│   ├── invoices/            # Invoice processing
│   ├── exports/             # Export functionality
│   ├── static/              # Static files
│   ├── templates/           # HTML templates
│   └── utils/               # Utilities
├── tests/                   # Test suite
├── docker-compose.yml       # Docker config
├── requirements.txt         # Dependencies
└── README.md               # Documentation
```

### Adding New Features

1. **Create module** in appropriate directory
2. **Add models** if needed in `models.py`
3. **Create routes** in module's `routes.py`
4. **Add templates** in `templates/`
5. **Write tests** in `tests/`
6. **Update documentation**

### Database Changes

1. **Modify models** in `models.py`
2. **Create migration**:
   ```bash
   docker-compose exec web flask db migrate -m "Description"
   ```
3. **Review migration** in `migrations/versions/`
4. **Apply migration**:
   ```bash
   docker-compose exec web flask db upgrade
   ```
5. **Test migration**:
   ```bash
   docker-compose exec web flask db downgrade
   docker-compose exec web flask db upgrade
   ```

## Areas for Contribution

### High Priority

- [ ] Multi-currency conversion
- [ ] Custom category management UI
- [ ] Duplicate invoice detection
- [ ] Email notifications
- [ ] Batch comparison analytics

### Medium Priority

- [ ] Advanced search and filters
- [ ] Invoice approval workflow
- [ ] Audit trail
- [ ] Performance optimizations
- [ ] Additional export formats

### Low Priority

- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Mobile app
- [ ] API documentation
- [ ] Internationalization

### Documentation

- [ ] Video tutorials
- [ ] API documentation
- [ ] Architecture diagrams
- [ ] Deployment guides
- [ ] Troubleshooting guides

## Questions?

- Open an issue for bugs
- Start a discussion for questions
- Check existing issues first
- Be specific and provide examples

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Invoice Processor! 🎉
