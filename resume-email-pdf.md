# Resume: Gmail Email Attachment Finder Module

## Status
**Planning complete, ready for implementation.**

---

## What to Tell Claude on the Other Machine

Copy and paste this prompt:

```
I'm continuing work on the invoice_app. Please implement the Gmail Email Attachment Finder module as planned in resume-email-pdf.md. This module should:

1. Search Gmail using native search syntax
2. Show summary of attachment types (PDFs, images, etc.)
3. Allow downloading all PDFs as a ZIP file via browser
4. Optional date range filtering
5. Optional: process downloaded PDFs through existing invoice system

The plan details are in this file. Please implement it phase by phase.
```

---

## Implementation Plan

### Phase 1: OAuth Scope Update

**File:** `app/auth/google_auth.py` (line 26-32)

Add Gmail readonly scope:
```python
self.scopes = [
    'openid',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/gmail.readonly'  # NEW
]
```

**Note:** Existing users will need to re-authenticate to grant Gmail permission.

---

### Phase 2: Create Emails Blueprint

#### File Structure
```
app/emails/
├── __init__.py         # Blueprint definition
├── routes.py           # Route handlers
└── gmail_handler.py    # Gmail API service class

app/templates/emails/
├── search.html         # Search form with date filters
└── results.html        # Results with attachment summary
```

#### Blueprint Definition
**New file:** `app/emails/__init__.py`
```python
from flask import Blueprint
emails_bp = Blueprint('emails', __name__)
from app.emails import routes
```

#### Register Blueprint
**File:** `app/__init__.py`
- Import `emails_bp`
- Register with prefix `/emails`

---

### Phase 3: Gmail Handler Service

**New file:** `app/emails/gmail_handler.py`

Key methods:
| Method | Purpose |
|--------|---------|
| `search_emails(query, max_results, page_token)` | Search Gmail with pagination |
| `get_message_with_attachments(message_id)` | Get email details + attachment metadata |
| `download_attachment(message_id, attachment_id)` | Download attachment content |
| `aggregate_attachment_summary(messages)` | Count attachments by type (PDF, image, etc.) |
| `build_date_query(date_from, date_to)` | Build Gmail date filter string |

Pattern reference: `app/invoices/drive_handler.py`

---

### Phase 4: Routes

**File:** `app/emails/routes.py`

| Route | Method | Purpose |
|-------|--------|---------|
| `/emails/search` | GET | Display search form |
| `/emails/search` | POST | Execute search, store params in session, redirect |
| `/emails/results` | GET | Display results with attachment summary |
| `/emails/download` | POST | Download selected PDFs as ZIP |
| `/emails/process` | POST | (Optional) Create invoice batch from PDFs |

---

### Phase 5: Templates

#### Search Page (`templates/emails/search.html`)
- Search query input (Gmail syntax)
- Optional date range pickers
- Help text with Gmail search examples
- Submit button

#### Results Page (`templates/emails/results.html`)
- **Summary cards**: Total attachments, PDF count, Image count, Other
- **Email list table**: Subject, From, Date, Attachments (with checkboxes for PDFs)
- **Action buttons**: "Download All PDFs", "Download Selected", "Process as Invoices"
- **Pagination**: Load more button if `next_page_token` exists

---

### Phase 6: Download Implementation

ZIP download flow:
1. Receive list of `{message_id, attachment_id, filename}`
2. Download each attachment via Gmail API
3. Create in-memory ZIP file
4. Return as browser download

Size limit: 50MB total to prevent memory issues.

---

### Phase 7: Navigation Updates

**File:** `app/templates/base.html`
- Add "Gmail Search" link with envelope icon in navbar

**File:** `app/templates/dashboard.html`
- Add quick action card/button for Gmail search

---

## Files Summary

### Files to Modify
| File | Changes |
|------|---------|
| `app/auth/google_auth.py` | Add Gmail readonly scope |
| `app/__init__.py` | Register emails blueprint |
| `app/templates/base.html` | Add Gmail Search nav link |
| `app/templates/dashboard.html` | Add Gmail action button |

### New Files to Create
| File | Purpose |
|------|---------|
| `app/emails/__init__.py` | Blueprint definition |
| `app/emails/routes.py` | All route handlers |
| `app/emails/gmail_handler.py` | Gmail API service class |
| `app/templates/emails/search.html` | Search form |
| `app/templates/emails/results.html` | Results display |

---

## Verification Checklist

1. [ ] Log out, log back in - verify Gmail permission requested
2. [ ] Search for "invoice has:attachment" - verify results appear
3. [ ] Verify PDF/image counts are accurate in summary
4. [ ] Select PDFs, download ZIP, verify contents open correctly
5. [ ] Test date range filter works
6. [ ] Test "Process as Invoices" creates a batch (optional)

---

## Key Patterns to Follow

- **Blueprint pattern**: See `app/settings/` or `app/invoices/`
- **Google API usage**: See `app/invoices/drive_handler.py`
- **Template structure**: Extend `base.html`, follow `app/templates/invoices/` patterns
- **File download**: See `app/invoices/routes.py` `view_pdf()` for Response pattern
