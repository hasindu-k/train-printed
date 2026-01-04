# Document OCR FastAPI Backend

A FastAPI backend for document processing and OCR with database models for documents, pages, line images, and users.

## Project Structure

```
api/
├── app/
│   ├── models/
│   │   └── __init__.py          # SQLAlchemy models
│   ├── routes/
│   │   ├── users.py             # User endpoints
│   │   ├── documents.py         # Document endpoints
│   │   ├── pages.py             # Page endpoints
│   │   ├── line_images.py       # Line image endpoints
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py          # Pydantic schemas
│   ├── database.py              # Database configuration
│   ├── main.py                  # FastAPI application
│   └── __init__.py
├── requirements.txt             # Project dependencies
├── .env.example                 # Environment variables example
└── README.md                    # This file
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate the virtual environment

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python -m uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Interactive API docs (Swagger UI):** http://localhost:8000/docs
- **Alternative API docs (ReDoc):** http://localhost:8000/redoc

## Database Models

### Users
- `id` (UUID): Primary key
- `name` (str): User name
- `email` (str): Unique email address
- `role` (str): admin, reviewer, annotator
- `created_at` (datetime): Creation timestamp

### Documents
- `id` (UUID): Primary key
- `original_filename` (str): Original file name
- `stored_path` (str): Path to stored file
- `status` (str): uploaded, processing, processed, failed
- `total_pages` (int): Number of pages
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

### Pages
- `id` (UUID): Primary key
- `document_id` (UUID): Foreign key to Document
- `page_number` (int): Page number
- `tif_path` (str): Path to TIF file
- `status` (str): pending, processed, failed
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

### LineImages
- `id` (UUID): Primary key
- `page_id` (UUID): Foreign key to Page
- `image_path` (str): Path to line image
- `auto_text` (str): Auto-extracted text
- `corrected_text` (str): Manually corrected text
- `verified` (bool): Whether the text is verified
- `reviewer_id` (UUID): Foreign key to User (nullable)
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

## API Endpoints

### Users
- `POST /users` - Create user
- `GET /users` - List users
- `GET /users/{user_id}` - Get user
- `PUT /users/{user_id}` - Update user
- `DELETE /users/{user_id}` - Delete user

### Documents
- `POST /documents` - Create document
- `GET /documents` - List documents
- `GET /documents/{document_id}` - Get document
- `PUT /documents/{document_id}` - Update document
- `DELETE /documents/{document_id}` - Delete document

### Pages
- `POST /pages?document_id={id}` - Create page
- `GET /pages?document_id={id}` - List pages
- `GET /pages/{page_id}` - Get page
- `PUT /pages/{page_id}` - Update page
- `DELETE /pages/{page_id}` - Delete page

### Line Images
- `POST /line-images?page_id={id}` - Create line image
- `GET /line-images?page_id={id}` - List line images
- `GET /line-images/{line_image_id}` - Get line image
- `PUT /line-images/{line_image_id}` - Update line image
- `DELETE /line-images/{line_image_id}` - Delete line image

## Example Usage

```bash
# Create a user
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe", "email": "john@example.com", "role": "reviewer"}'

# Create a document
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -d '{"original_filename": "document.pdf", "stored_path": "/path/to/file"}'

# Get all documents
curl http://localhost:8000/documents
```

## Development

To make changes to the code and have them automatically reload:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Notes

- This project uses SQLite by default for simplicity
- For production, switch to PostgreSQL by updating the `SQLALCHEMY_DATABASE_URL`
- Add authentication/authorization as needed
- Add input validation and error handling as needed
