# API Documentation

Complete API reference for the Invoice Processor application.

## Base URL

```
Local: http://localhost:5000
Production: https://yourdomain.com
```

## Authentication

All API endpoints (except public pages) require authentication via Google OAuth.

### Authentication Flow

1. **Initiate Login**
   ```
   GET /auth/login
   ```
   Redirects to Google OAuth consent screen.

2. **OAuth Callback**
   ```
   GET /auth/callback?code=...&state=...
   ```
   Handles OAuth callback and creates session.

3. **Logout**
   ```
   GET /auth/logout
   ```
   Clears session and logs out user.

## Endpoints

### Public Endpoints

#### Landing Page
```http
GET /
```

**Response**: HTML landing page

**Status Codes**:
- `200 OK` - Success
- `302 Found` - Redirect if authenticated

---

### Invoice Processing

#### Upload Form
```http
GET /invoices/upload
```

**Authentication**: Required

**Response**: HTML upload form

**Status Codes**:
- `200 OK` - Success
- `302 Found` - Redirect to login if not authenticated

---

#### Start Processing
```http
POST /invoices/process
```

**Authentication**: Required

**Request Body** (form-data):
```
drive_url: string (required) - Google Drive folder URL
```

**Example**:
```bash
curl -X POST http://localhost:5000/invoices/process \
  -H "Cookie: session=..." \
  -F "drive_url=https://drive.google.com/drive/folders/abc123"
```

**Response**: Redirect to processing page

**Status Codes**:
- `302 Found` - Redirect to processing page
- `400 Bad Request` - Invalid URL
- `401 Unauthorized` - Not authenticated

---

#### Processing Status Page
```http
GET /invoices/processing/<batch_id>
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Response**: HTML progress page with real-time updates

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized

---

#### Batch Status (API)
```http
GET /invoices/batch/<batch_id>
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Response** (JSON):
```json
{
  "id": 1,
  "status": "processing",
  "total_invoices": 50,
  "processed_invoices": 25,
  "failed_invoices": 2,
  "progress_percentage": 50,
  "error_message": null
}
```

**Status Values**:
- `pending` - Waiting to start
- `processing` - Currently processing
- `completed` - Finished successfully
- `failed` - Processing failed

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized

---

#### Batch Summary
```http
GET /invoices/batch/<batch_id>/summary
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Response**: HTML summary dashboard with charts

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized

---

#### Batch Details
```http
GET /invoices/batch/<batch_id>/details
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Response**: HTML detailed invoice list

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized

---

#### Update Invoice Category
```http
PUT /invoices/<invoice_id>/category
```

**Authentication**: Required

**Parameters**:
- `invoice_id` (integer) - Invoice ID

**Request Body** (JSON):
```json
{
  "category": "Office Supplies"
}
```

**Example**:
```bash
curl -X PUT http://localhost:5000/invoices/123/category \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{"category": "Office Supplies"}'
```

**Response** (JSON):
```json
{
  "message": "Category updated successfully"
}
```

**Status Codes**:
- `200 OK` - Success
- `400 Bad Request` - Invalid category
- `404 Not Found` - Invoice not found
- `403 Forbidden` - Not authorized

---

#### Delete Batch
```http
DELETE /invoices/batch/<batch_id>
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Example**:
```bash
curl -X DELETE http://localhost:5000/invoices/batch/1 \
  -H "Cookie: session=..."
```

**Response** (JSON):
```json
{
  "message": "Batch deleted successfully"
}
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized

---

### Export Endpoints

#### Export to CSV
```http
GET /export/csv/<batch_id>
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Example**:
```bash
curl -X GET http://localhost:5000/export/csv/1 \
  -H "Cookie: session=..." \
  -o invoices.csv
```

**Response**: CSV file download

**CSV Format**:
```csv
Invoice Number,Vendor Name,Invoice Date,Amount,Currency,Category,Confidence,Filename,Status
INV-001,ACME Corp,2024-01-15,1000.00,USD,Office Supplies,95%,invoice1.pdf,categorized
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized
- `500 Internal Server Error` - Export failed

---

#### Export to Google Sheets
```http
POST /export/sheets/<batch_id>
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Request Body** (JSON, optional):
```json
{
  "spreadsheet_name": "Invoices - January 2024",
  "existing_spreadsheet_id": "abc123..."
}
```

**Example**:
```bash
curl -X POST http://localhost:5000/export/sheets/1 \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{"spreadsheet_name": "My Invoices"}'
```

**Response** (JSON):
```json
{
  "message": "Successfully exported to Google Sheets",
  "url": "https://docs.google.com/spreadsheets/d/abc123...",
  "spreadsheet_id": "abc123...",
  "sheet_name": "Batch 1"
}
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized
- `500 Internal Server Error` - Export failed

---

#### Export Summary to Google Sheets
```http
POST /export/sheets/<batch_id>/summary
```

**Authentication**: Required

**Parameters**:
- `batch_id` (integer) - Batch ID

**Response** (JSON):
```json
{
  "message": "Successfully exported summary to Google Sheets",
  "url": "https://docs.google.com/spreadsheets/d/abc123...",
  "spreadsheet_id": "abc123...",
  "sheet_name": "Summary"
}
```

**Status Codes**:
- `200 OK` - Success
- `404 Not Found` - Batch not found
- `403 Forbidden` - Not authorized
- `500 Internal Server Error` - Export failed

---

## Data Models

### Batch Object

```json
{
  "id": 1,
  "user_id": 1,
  "drive_url": "https://drive.google.com/drive/folders/abc123",
  "status": "completed",
  "total_invoices": 50,
  "processed_invoices": 48,
  "failed_invoices": 2,
  "total_amount": 125000.00,
  "currency": "USD",
  "date_range_start": "2024-01-01",
  "date_range_end": "2024-01-31",
  "created_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:15:00Z",
  "error_message": null
}
```

### Invoice Object

```json
{
  "id": 1,
  "batch_id": 1,
  "drive_file_id": "xyz789",
  "filename": "invoice_001.pdf",
  "vendor_name": "ACME Corporation",
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-15",
  "total_amount": 1250.00,
  "currency": "USD",
  "category": "Office Supplies",
  "category_confidence": 0.95,
  "extraction_method": "pdfplumber",
  "status": "categorized",
  "error_message": null,
  "created_at": "2024-01-15T10:05:00Z",
  "updated_at": "2024-01-15T10:05:30Z"
}
```

### Category Object

```json
{
  "id": 1,
  "name": "Office Supplies",
  "description": "Office supplies and stationery",
  "keywords": ["office", "supplies", "paper", "pens"],
  "is_default": true,
  "created_by": 1,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Default Categories

1. Office Supplies
2. Travel
3. Software & Technology
4. Professional Services
5. Utilities
6. Marketing & Advertising
7. Equipment & Hardware
8. Rent & Facilities
9. Insurance
10. Legal & Compliance
11. Training & Education
12. Meals & Entertainment
13. Telecommunications
14. Shipping & Delivery
15. Maintenance & Repairs
16. Other

## Error Responses

All error responses follow this format:

```json
{
  "error": "Error message description"
}
```

### Common Error Codes

- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not authorized to access resource
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error
- `501 Not Implemented` - Feature not yet implemented

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, consider adding rate limiting to prevent abuse.

## Webhooks

Webhooks are not currently supported but may be added in future versions.

## SDK / Client Libraries

No official SDK is currently available. Use standard HTTP clients:

### Python Example

```python
import requests

# Login (requires browser for OAuth)
session = requests.Session()

# Get batch status
response = session.get('http://localhost:5000/invoices/batch/1')
data = response.json()
print(f"Progress: {data['progress_percentage']}%")

# Update category
response = session.put(
    'http://localhost:5000/invoices/123/category',
    json={'category': 'Office Supplies'}
)
print(response.json())

# Export to CSV
response = session.get('http://localhost:5000/export/csv/1')
with open('invoices.csv', 'wb') as f:
    f.write(response.content)
```

### JavaScript Example

```javascript
// Get batch status
fetch('/invoices/batch/1')
  .then(response => response.json())
  .then(data => {
    console.log(`Progress: ${data.progress_percentage}%`);
  });

// Update category
fetch('/invoices/123/category', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({category: 'Office Supplies'})
})
  .then(response => response.json())
  .then(data => console.log(data.message));

// Export to Sheets
fetch('/export/sheets/1', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({spreadsheet_name: 'My Invoices'})
})
  .then(response => response.json())
  .then(data => window.open(data.url, '_blank'));
```

## Changelog

### Version 1.0.0 (2026-02-03)
- Initial API release
- All core endpoints implemented
- OAuth authentication
- CSV and Google Sheets export

---

**API Version**: 1.0.0
**Last Updated**: 2026-02-03
