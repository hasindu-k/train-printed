# API Endpoints Summary

## Base URL

`http://localhost:8000`

## Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI JSON:** `http://localhost:8000/openapi.json`

---

## 🔐 Authentication Endpoints

### POST /auth/register

Register a new user account

**Request:**

```json
{
  "name": "John Annotator",
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Response:** `201 Created`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Annotator",
    "email": "john@example.com",
    "role": "annotator",
    "is_active": true,
    "created_at": "2026-01-05T10:00:00"
  }
}
```

---

### POST /auth/login

Login with email and password

**Request:**

```json
{
  "email": "john@example.com",
  "password": "securepass123"
}
```

**Response:** `200 OK` (same as register)

---

### POST /auth/refresh

Refresh an expired access token

**Request:**

```json
{
  "refresh_token": "<your_refresh_token>"
}
```

**Response:** `200 OK` (new access and refresh tokens)

---

### GET /auth/me

Get current authenticated user information

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "John Annotator",
  "email": "john@example.com",
  "role": "annotator",
  "is_active": true,
  "created_at": "2026-01-05T10:00:00"
}
```

---

### POST /auth/logout

Logout current user (invalidates tokens on client)

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

---

## User Management

### POST /users/admin/create

Create a new user (Admin only)

**Headers:**

```
Authorization: Bearer <admin_access_token>
```

**Request:**

```json
{
  "name": "Jane Reviewer",
  "email": "jane@example.com",
  "password": "securepass456",
  "role": "reviewer"
}
```

**Response:** `201 Created`

```json
{
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "name": "Jane Reviewer",
  "email": "jane@example.com",
  "role": "reviewer",
  "is_active": true,
  "created_at": "2026-01-05T10:30:00"
}
```

---

### GET /users/

List all users (Admin only)

**Headers:**

```
Authorization: Bearer <admin_access_token>
```

**Response:** `200 OK`

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "John Annotator",
    "email": "john@example.com",
    "role": "annotator",
    "is_active": true,
    "created_at": "2026-01-05T10:00:00"
  }
]
```

---

### GET /users/{user_id}

Get specific user (User can view self, Admin can view anyone)

**Headers:**

```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

---

### PUT /users/{user_id}

Update user (User can update self, Admin can update anyone)

**Headers:**

```
Authorization: Bearer <access_token>
```

**Request:**

```json
{
  "name": "John Updated",
  "email": "john.new@example.com",
  "role": "reviewer" // only admin can change role
}
```

**Response:** `200 OK`

---

### DELETE /users/{user_id}

Delete user (Admin only)

**Headers:**

```
Authorization: Bearer <admin_access_token>
```

**Response:** `204 No Content`

---

## Health Check

### GET /health

Check API health status

**Response:**

```json
{
  "status": "healthy"
}
```

"id": "uuid",
"name": "John Reviewer",
"email": "john@example.com",
"role": "reviewer",
"created_at": "2024-01-05T..."
}

````

### GET /users

List all users

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "name": "John Reviewer",
    "email": "john@example.com",
    "role": "reviewer",
    "created_at": "..."
  }
]
````

### GET /users/{user_id}

Get a specific user

**Response:** `200 OK`

### PUT /users/{user_id}

Update user

**Request:**

```json
{
  "name": "Updated Name",
  "email": "newemail@example.com",
  "role": "admin"
}
```

### DELETE /users/{user_id}

Delete user

**Response:** `204 No Content`

---

## Document Management

### POST /documents/upload

Upload a PDF file

**Request:**

```
Content-Type: multipart/form-data
file: <binary PDF file>
```

**Response:** `201 Created`

```json
{
  "id": "uuid",
  "original_filename": "document.pdf",
  "stored_path": "uploads/document.pdf",
  "pages_folder": "pages/document",
  "status": "uploaded",
  "total_pages": 0,
  "created_at": "2024-01-05T...",
  "updated_at": "2024-01-05T..."
}
```

### GET /documents

List all documents

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "original_filename": "document.pdf",
    "stored_path": "uploads/document.pdf",
    "pages_folder": "pages/document",
    "status": "uploaded",
    "total_pages": 10,
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### GET /documents/{document_id}

Get a specific document

### PUT /documents/{document_id}

Update document metadata

**Request:**

```json
{
  "status": "processed",
  "total_pages": 10
}
```

### DELETE /documents/{document_id}

Delete document and all associated files

**Response:** `204 No Content`

### POST /documents/{document_id}/convert-pages

Convert PDF to TIFF pages

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "status": "processed",
  "total_pages": 10,
  ...
}
```

**Creates:**

- Folder: `pages/document_name/`
- Files: `page_0001.tif`, `page_0002.tif`, ...
- DB records in `pages` table

### GET /documents/{document_id}/pages

List all pages in a document

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "document_id": "uuid",
    "page_number": 1,
    "tif_path": "pages/document/page_0001.tif",
    "status": "pending",
    "created_at": "...",
    "updated_at": "..."
  }
]
```

### POST /documents/{document_id}/create-gt-files

Create ground truth text files for all lines (bulk)

**Response:** `200 OK`

```json
{
  "status": "success",
  "document_id": "uuid",
  "gt_files_created": 150
}
```

### GET /documents/{document_id}/lines

Fetch lines for labeling with optional filters

**Query Parameters:**

- `verified` (bool): Filter by verification status
- `page_num` (int): Filter by page number
- `assigned_to` (uuid): Filter by reviewer

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "page_id": "uuid",
    "image_path": "lines/document/page_0001/line_0001.tif",
    "auto_text": "detected text",
    "corrected_text": null,
    "verified": false,
    "reviewer_id": null
  }
]
```

### GET /documents/{document_id}/export

Export dataset as ZIP file

**Response:** `200 OK`

```json
{
  "status": "success",
  "download_url": "/downloads/document_dataset.zip",
  "file_path": "uploads/exports/document_dataset.zip"
}
```

---

## Page Management

### POST /pages

Create a page (manually)

**Request:**

```json
{
  "page_number": 1,
  "tif_path": "pages/document/page_0001.tif"
}
```

**Query Parameters:**

- `document_id` (uuid, required)

### GET /pages

List pages

**Query Parameters:**

- `document_id` (uuid, optional)

### GET /pages/{page_id}

Get a specific page

### PUT /pages/{page_id}

Update page

**Request:**

```json
{
  "status": "processed"
}
```

### DELETE /pages/{page_id}

Delete page

**Response:** `204 No Content`

### POST /documents/{document_id}/pages/{page_id}/extract-lines

Extract line images from a page

**Response:** `200 OK`

```json
{
  "status": "success",
  "page_id": "uuid",
  "lines_extracted": 25
}
```

**Creates:**

- Folder: `lines/document_name/page_XXXX/`
- Files: `line_0001.tif`, `line_0002.tif`, ...
- DB records in `line_images` table

### POST /documents/{document_id}/pages/{page_id}/create-gt-files

Create ground truth files for a page

**Response:** `200 OK`

```json
{
  "status": "success",
  "page_id": "uuid",
  "gt_files_created": 25
}
```

---

## Line Image Management

### GET /lines/{line_id}

Get line image with all metadata

**Response:** `200 OK`

```json
{
  "id": "uuid",
  "page_id": "uuid",
  "image_path": "lines/document/page_0001/line_0001.tif",
  "image_url": "/lines/uuid/image",
  "gt_text_path": "lines/document/page_0001/line_0001.gt.txt",
  "auto_text": "detected text",
  "corrected_text": null,
  "gt_text_content": "",
  "verified": false,
  "is_invalid": false,
  "reviewer_id": null,
  "created_at": "2024-01-05T...",
  "updated_at": "2024-01-05T..."
}
```

### GET /lines/{line_id}/image

Get the line image file

**Response:** `200 OK` (image/tiff)

### PUT /lines/{line_id}/corrected-text

Save corrected text and update .gt.txt file

**Request:**

```json
{
  "corrected_text": "සිංහල පදය"
}
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "line_id": "uuid",
  "corrected_text": "සිංහල පදය",
  "gt_file_updated": true
}
```

### PUT /lines/{line_id}/verify

Mark line as verified

**Request:**

```json
{
  "reviewer_id": "uuid"
}
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "line_id": "uuid",
  "verified": true
}
```

### PUT /lines/{line_id}/unverify

Mark line as unverified

**Response:** `200 OK`

```json
{
  "status": "success",
  "line_id": "uuid",
  "verified": false
}
```

### PUT /lines/{line_id}

Update line image (generic)

**Request:**

```json
{
  "corrected_text": "updated text",
  "verified": true,
  "reviewer_id": "uuid"
}
```

### DELETE /lines/{line_id}

Soft-delete (mark as invalid) a line image. To permanently remove the DB row and files, pass `?hard=true`.

**Query params:**

- `hard` (boolean, default `false`): when `true`, permanently deletes and removes image/png/gt files from disk.

**Response:** `204 No Content`

### PUT /lines/{line_id}/invalidate

Mark a line as invalid (bad crop). Reviewer/Admin only.

**Response:** `200 OK`

```json
{ "status": "success", "line_id": "uuid", "is_invalid": true }
```

### PUT /lines/{line_id}/restore

Restore a previously invalid line (set `is_invalid=false`). Reviewer/Admin only.

**Response:** `200 OK`

```json
{ "status": "success", "line_id": "uuid", "is_invalid": false }
```

### GET /lines/page/{page_id}/all

Get all lines for a page. Excludes invalid lines by default; include them with `?include_invalid=true`.

**Response:** `200 OK`

```json
[
  {
    "id": "uuid",
    "page_id": "uuid",
    "image_path": "...",
    "auto_text": "...",
    "corrected_text": "...",
    "verified": false,
    "is_invalid": false
  }
]
```

---

## Error Responses

All endpoints return appropriate HTTP status codes:

- `200 OK` - Success
- `201 Created` - Resource created
- `204 No Content` - Deleted successfully
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

**Error Response Format:**

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## File Serving

Static files are served from these paths:

- `/uploads/` - Uploaded PDFs
- `/pages/` - Extracted TIFF pages
- `/lines/` - Extracted line images

Example:

```
GET /uploads/document.pdf
GET /pages/document/page_0001.tif
GET /lines/document/page_0001/line_0001.tif
```

---

## Request/Response Formats

All endpoints use JSON for request/response bodies (except file uploads).

**Headers:**

```
Content-Type: application/json
Accept: application/json
```

**Authentication:** (To be added)
Currently no authentication. Add JWT tokens in headers once implemented:

```
Authorization: Bearer <token>
```

---

## Rate Limiting

Currently no rate limiting. Recommended for production:

- User creation: 10 req/min
- File upload: 5 req/min
- Other endpoints: 100 req/min

---

## Pagination

Future enhancement for list endpoints:

```
GET /documents?skip=0&limit=10
```

---

## Changelog

### v1.0.0 (Current)

- Initial release
- PDF upload and processing
- TIFF conversion
- Line extraction
- GT text file management
- Line correction and verification
- Dataset export
