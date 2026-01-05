# Document OCR & Tesseract Training API

A FastAPI backend for processing document images, extracting lines, managing ground truth text files, and preparing training datasets for Tesseract OCR.

## Features

✅ **JWT Authentication** - Secure token-based user authentication
✅ **Role-Based Access Control** - admin, reviewer, annotator roles
✅ **Password Security** - bcrypt password hashing
✅ PDF upload and processing
✅ PDF to TIFF conversion (multi-page)
✅ Line extraction from pages using OpenCV
✅ Ground truth text file management
✅ **User Management** - Create, manage, and control user access
✅ Line image correction and verification workflow
✅ Dataset export for Tesseract training
✅ User role management (admin, reviewer, annotator)
✅ File serving and management
✅ RESTful API with Swagger/OpenAPI documentation

## Project Structure

```
api/
├── app/
│   ├── models/
│   │   └── __init__.py          # SQLAlchemy ORM models
│   ├── routes/
│   │   ├── users.py             # User management
│   │   ├── documents.py         # Document & workflow endpoints
│   │   ├── pages.py             # Page management
│   │   ├── line_images.py       # Line correction & verification
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py          # Pydantic request/response schemas
│   ├── database.py              # Database configuration
│   ├── main.py                  # FastAPI application
│   ├── utils.py                 # Utility functions for image processing
│   └── __init__.py
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment variables example
└── README.md                    # This file
```

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install system dependencies (for pdf2image)

**Windows:**

```bash
# Download poppler from https://github.com/oschwartz10612/poppler-windows/releases/
# Or install via chocolatey:
choco install poppler
```

**macOS:**

```bash
brew install poppler
```

**Linux (Ubuntu):**

```bash
sudo apt-get install poppler-utils
```

### 3. Create virtual environment (optional but recommended)

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### 4. Run the application

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Interactive API docs (Swagger UI):** http://localhost:8000/docs
- **Alternative API docs (ReDoc):** http://localhost:8000/redoc

## 🔐 Authentication

### Quick Start with Auth

```bash
# 1. Register a new user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John User",
    "email": "john@example.com",
    "password": "securepass123"
  }'

# Response includes access_token - save it!

# 2. Use the token for authenticated requests
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <your_access_token>"

# 3. Upload a document
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Authorization: Bearer <your_access_token>" \
  -F "file=@document.pdf"
```

### Authentication Features

- ✅ **JWT Tokens** - Secure token-based authentication
- ✅ **Token Refresh** - Long-lived refresh tokens for extended sessions
- ✅ **Role-Based Access** - Control who can do what:
  - **Admin**: Full access, user management
  - **Reviewer**: Verify lines, manage documents
  - **Annotator**: Correct lines, upload documents
- ✅ **Password Hashing** - bcrypt for secure storage

**For full authentication documentation, see [AUTHENTICATION.md](AUTHENTICATION.md)**

## Complete Workflow

### 1️⃣ Upload & Register Document

```bash
POST /documents/upload
Content-Type: multipart/form-data

file: <your-pdf-file.pdf>
```

**Response:**

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

### 2️⃣ Convert PDF → TIFF Pages

```bash
POST /documents/{document_id}/convert-pages
```

**Response:**

```json
{
  "id": "uuid",
  "status": "processed",
  "total_pages": 10,
  ...
}
```

Creates:

- Folder: `pages/document_name/`
- Files: `page_0001.tif`, `page_0002.tif`, ...
- DB records in `pages` table

### 3️⃣ List Pages

```bash
GET /documents/{document_id}/pages
```

**Response:**

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
  },
  ...
]
```

### 4️⃣ Extract Line Images from a Page

```bash
POST /documents/{document_id}/pages/{page_id}/extract-lines
```

**Response:**

```json
{
  "status": "success",
  "page_id": "uuid",
  "lines_extracted": 25
}
```

Creates:

- Folder: `lines/document_name/page_0001/`
- Files: `line_0001.tif`, `line_0002.tif`, ...
- DB records in `line_images` table

### 5️⃣ Create Ground Truth Text Files

**Per page:**

```bash
POST /documents/{document_id}/pages/{page_id}/create-gt-files
```

**Bulk for entire document:**

```bash
POST /documents/{document_id}/create-gt-files
```

**Response:**

```json
{
  "status": "success",
  "document_id": "uuid",
  "gt_files_created": 150
}
```

Creates empty `.gt.txt` files:

- `line_0001.gt.txt`
- `line_0002.gt.txt`
- ...

### 6️⃣ Fetch Lines for Labeling

```bash
GET /documents/{document_id}/lines?verified=false&page=1&assigned_to={user_id}
```

**Query parameters:**

- `verified` (bool): Filter by verification status
- `page_num` (int): Filter by page number
- `assigned_to` (uuid): Filter by reviewer

**Response:**

```json
[
  {
    "id": "uuid",
    "page_id": "uuid",
    "image_path": "lines/document/page_0001/line_0001.tif",
    "auto_text": "detected text",
    "corrected_text": "corrected text",
    "verified": false,
    "reviewer_id": null
  },
  ...
]
```

### 7️⃣ Get Line Image + Text

```bash
GET /lines/{line_id}
```

**Response:**

```json
{
  "id": "uuid",
  "page_id": "uuid",
  "image_path": "lines/document/page_0001/line_0001.tif",
  "image_url": "/lines/uuid/image",
  "gt_text_path": "lines/document/page_0001/line_0001.gt.txt",
  "auto_text": "detected text",
  "corrected_text": "corrected text",
  "gt_text_content": "corrected text",
  "verified": false,
  "reviewer_id": null,
  "created_at": "...",
  "updated_at": "..."
}
```

### 8️⃣ Save Corrected GT Text

```bash
PUT /lines/{line_id}/corrected-text

{
  "corrected_text": "සිංහල පදය"
}
```

**Response:**

```json
{
  "status": "success",
  "line_id": "uuid",
  "corrected_text": "සිංහල පදය",
  "gt_file_updated": true
}
```

**Backend:**

- ✔ Updates `corrected_text` in DB
- ✔ Updates `.gt.txt` file on disk
- ✔ Does NOT overwrite `auto_text`

### 9️⃣ Verify Line

```bash
PUT /lines/{line_id}/verify

{
  "reviewer_id": "uuid"  # optional
}
```

**Response:**

```json
{
  "status": "success",
  "line_id": "uuid",
  "verified": true
}
```

### Unverify Line

```bash
PUT /lines/{line_id}/unverify
```

**Response:**

```json
{
  "status": "success",
  "line_id": "uuid",
  "verified": false
}
```

### 🔟 Export Dataset for Training

```bash
GET /documents/{document_id}/export
```

**Response:**

```json
{
  "status": "success",
  "download_url": "/downloads/document_dataset.zip",
  "file_path": "uploads/exports/document_dataset.zip"
}
```

**Exports:**

- `line_0001.tif`, `line_0001.gt.txt`
- `line_0002.tif`, `line_0002.gt.txt`
- ... (all lines and their ground truth files)

## Database Models

### Users

- `id` (UUID): Primary key
- `name` (str): User name
- `email` (str): Unique email
- `role` (str): admin | reviewer | annotator
- `created_at` (datetime)

### Documents

- `id` (UUID): Primary key
- `original_filename` (str)
- `stored_path` (str): Path to uploaded PDF
- `pages_folder` (str): Path to extracted TIFF pages
- `status` (str): uploaded | processing | processed | failed
- `total_pages` (int)
- `created_at` (datetime)
- `updated_at` (datetime)

### Pages

- `id` (UUID): Primary key
- `document_id` (UUID): FK → documents
- `page_number` (int)
- `tif_path` (str): Path to TIFF file
- `status` (str): pending | processed | failed
- `created_at` (datetime)
- `updated_at` (datetime)

### LineImages

- `id` (UUID): Primary key
- `page_id` (UUID): FK → pages
- `image_path` (str): Path to line TIFF
- `gt_text_path` (str): Path to .gt.txt file
- `auto_text` (str): Auto-extracted text
- `corrected_text` (str): Manually corrected text
- `verified` (bool): Verification status
- `reviewer_id` (UUID): FK → users (nullable)
- `created_at` (datetime)
- `updated_at` (datetime)

## Example Usage

### Complete Workflow Example

```bash
# 1. Upload PDF
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@book.pdf"
# Returns: document_id

# 2. Convert to TIFF pages
curl -X POST http://localhost:8000/documents/{document_id}/convert-pages

# 3. Extract lines from page 1
curl -X POST http://localhost:8000/documents/{document_id}/pages/{page_id}/extract-lines

# 4. Create ground truth files for all
curl -X POST http://localhost:8000/documents/{document_id}/create-gt-files

# 5. Get unverified lines
curl http://localhost:8000/documents/{document_id}/lines?verified=false

# 6. Get a line with image
curl http://localhost:8000/lines/{line_id}

# 7. Correct text
curl -X PUT http://localhost:8000/lines/{line_id}/corrected-text \
  -H "Content-Type: application/json" \
  -d '{"corrected_text": "corrected word"}'

# 8. Mark as verified
curl -X PUT http://localhost:8000/lines/{line_id}/verify \
  -H "Content-Type: application/json" \
  -d '{"reviewer_id": "{user_id}"}'

# 9. Export dataset
curl -X GET http://localhost:8000/documents/{document_id}/export \
  -o dataset.zip
```

## Configuration

### Database

By default, SQLite is used. To use PostgreSQL:

**Update** `app/database.py`:

```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"
```

Install PostgreSQL driver:

```bash
pip install psycopg2-binary
```

## Development

### Auto-reload on changes

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run in production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Troubleshooting

### PDF conversion fails

- Ensure poppler is installed correctly
- Check file permissions on output directories
- Verify PDF is not corrupted

### Line extraction issues

- Check image quality and DPI
- Adjust kernel size in `utils.py` if needed
- Ensure TIFF files are valid

### File not found errors

- Verify upload directory permissions
- Check file paths are correct
- Ensure cleanup removes broken references

## Future Enhancements

- [ ] Auto-OCR integration (Tesseract)
- [ ] Batch processing with Celery
- [ ] Image preprocessing pipeline
- [ ] Advanced filtering and search
- [ ] Performance metrics and analytics
- [ ] User authentication and authorization
- [ ] API rate limiting

## License

MIT
