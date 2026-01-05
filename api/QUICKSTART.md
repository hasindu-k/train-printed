# FastAPI Backend - Quick Start Guide

## Prerequisites

- Python 3.8+
- Poppler (for PDF to image conversion)

## Installation Steps

### 1. Install Poppler

**Windows (using Chocolatey):**

```bash
choco install poppler
```

Or download from: https://github.com/oschwartz10612/poppler-windows/releases/

**macOS:**

```bash
brew install poppler
```

**Ubuntu/Debian:**

```bash
sudo apt-get install poppler-utils
```

### 2. Create Virtual Environment

```bash
cd c:\github\train-printed\api
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
python -m uvicorn app.main:app --reload
```

Server runs at: **http://localhost:8000**

## Quick Test

Open your browser and go to: **http://localhost:8000/docs**

This opens the interactive API documentation where you can test all endpoints.

## Typical Workflow

```bash
# 1. Upload a PDF
POST /documents/upload
(select file from form)

# 2. Convert to TIFF pages
POST /documents/{document_id}/convert-pages

# 3. Extract lines from a page
POST /documents/{document_id}/pages/{page_id}/extract-lines

# 4. Create ground truth files
POST /documents/{document_id}/create-gt-files

# 5. View unverified lines
GET /documents/{document_id}/lines?verified=false

# 6. Get a line
GET /lines/{line_id}

# 7. Correct text
PUT /lines/{line_id}/corrected-text
{"corrected_text": "corrected text"}

# 8. Verify
PUT /lines/{line_id}/verify

# 9. Export dataset
GET /documents/{document_id}/export
```

## File Structure Created

```
api/
├── uploads/          # PDF files stored here
├── pages/            # TIFF pages extracted here
├── lines/            # Line images extracted here
├── app/
│   ├── main.py       # Main FastAPI app
│   ├── database.py   # Database setup
│   ├── utils.py      # Image processing functions
│   ├── models/       # Database models
│   ├── routes/       # API endpoints
│   └── schemas/      # Request/response models
└── requirements.txt
```

## Database

SQLite database is automatically created: `test.db`

To use PostgreSQL instead:

1. Install: `pip install psycopg2-binary`
2. Update `SQLALCHEMY_DATABASE_URL` in `app/database.py`

## Troubleshooting

### Module not found errors

```bash
pip install -r requirements.txt --upgrade
```

### PDF conversion fails

- Check poppler is installed: `where pdftoimage` (Windows)
- Verify PDF is valid
- Check permissions on output directories

### Port 8000 already in use

```bash
python -m uvicorn app.main:app --reload --port 8001
```

## Next Steps

Create a Next.js frontend to:

- Upload PDFs
- Display pages
- Annotate lines
- Review corrections
- Export datasets

See `api/README.md` for complete API documentation.
