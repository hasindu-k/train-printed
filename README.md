# Tesseract Training Dataset Manager

Complete solution for creating, managing, and preparing training datasets for **Tesseract OCR** with focus on **Sinhala printed text**.

## 📦 Project Structure

```
train-printed/
├── api/                          # FastAPI Backend (NEW)
│   ├── app/                      # Application code
│   ├── requirements.txt          # Python dependencies
│   ├── README.md                 # Backend documentation
│   ├── QUICKSTART.md             # Quick start guide
│   ├── API_ENDPOINTS.md          # API reference
│   ├── SUMMARY.md                # Implementation summary
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── FRONTEND_GUIDE.md          # Frontend setup guide
│   └── test_api.py               # API testing script
│
├── create_gt_text_files.py       # Create empty .gt.txt files
├── pdf_to_tif.py                 # Convert PDF to TIFF pages
├── seperate_lines.py             # Extract line images
└── README.md                     # This file
```

## 🎯 What This Project Does

1. **Upload Books** - Upload PDF books/documents
2. **Extract Pages** - Convert PDF to TIFF page images (300 DPI)
3. **Extract Lines** - Extract individual text lines from pages
4. **Create Ground Truth** - Create empty .gt.txt files for each line
5. **Annotate** - Correct and verify text for each line
6. **Export** - Package lines with corrected text for Tesseract training

## 🚀 Quick Start

### Backend Setup

```bash
cd api

# Install dependencies
pip install -r requirements.txt

# Install system dependency (poppler)
# Windows: choco install poppler
# macOS: brew install poppler
# Ubuntu: sudo apt-get install poppler-utils

# Run server
python -m uvicorn app.main:app --reload

# Access API documentation
# http://localhost:8000/docs
```

### Test the API

```bash
python test_api.py
```

## 📚 Documentation

### For Backend Development

- **[README.md](api/README.md)** - Complete API documentation and setup
- **[QUICKSTART.md](api/QUICKSTART.md)** - Quick start guide
- **[API_ENDPOINTS.md](api/API_ENDPOINTS.md)** - All 20+ endpoints reference
- **[SUMMARY.md](api/SUMMARY.md)** - Implementation summary
- **[DEPLOYMENT.md](api/DEPLOYMENT.md)** - Production deployment

### For Frontend Development

- **[FRONTEND_GUIDE.md](api/FRONTEND_GUIDE.md)** - Next.js integration guide

## 🔄 Workflow

### Step 1: Upload Document

```bash
POST /documents/upload
```

Upload a PDF file → Returns document_id

### Step 2: Convert to TIFF

```bash
POST /documents/{document_id}/convert-pages
```

PDF → Extract pages as TIFF images

### Step 3: Extract Lines

```bash
POST /documents/{document_id}/pages/{page_id}/extract-lines
```

Page image → Extract individual text lines

### Step 4: Create GT Files

```bash
POST /documents/{document_id}/create-gt-files
```

Create empty .gt.txt for each line

### Step 5: Annotate

```bash
PUT /lines/{line_id}/corrected-text
```

Correct text for each line

### Step 6: Verify

```bash
PUT /lines/{line_id}/verify
```

Mark lines as verified

### Step 7: Export

```bash
GET /documents/{document_id}/export
```

Download ZIP with TIF + GT.txt pairs

## 🗄️ Database Schema

### 4 Main Tables

- **users** - User accounts (admin, reviewer, annotator)
- **documents** - Uploaded PDFs with processing status
- **pages** - TIFF pages extracted from PDFs
- **line_images** - Individual text lines with corrections

All tables use UUID primary keys, timestamps, and proper relationships.

## 📡 API Endpoints (20+)

### Document Management

- `POST /documents/upload` - Upload PDF
- `GET /documents` - List documents
- `GET /documents/{id}` - Get document
- `PUT /documents/{id}` - Update document
- `DELETE /documents/{id}` - Delete document

### Processing Pipeline

- `POST /documents/{id}/convert-pages` - PDF → TIFF
- `GET /documents/{id}/pages` - List pages
- `POST /documents/{id}/pages/{pid}/extract-lines` - Extract lines
- `POST /documents/{id}/create-gt-files` - Create GT files

### Line Annotation

- `GET /documents/{id}/lines` - Get lines (with filters)
- `GET /lines/{id}` - Get line details
- `PUT /lines/{id}/corrected-text` - Save correction
- `PUT /lines/{id}/verify` - Mark verified
- `PUT /lines/{id}/unverify` - Mark unverified

### Dataset

- `GET /documents/{id}/export` - Export as ZIP

### Users

- `POST /users` - Create user
- `GET /users` - List users
- `GET /users/{id}` - Get user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user

See [API_ENDPOINTS.md](api/API_ENDPOINTS.md) for complete reference.

## 🛠️ Technology Stack

### Backend

- **Framework:** FastAPI
- **Server:** Uvicorn
- **Database:** SQLAlchemy + SQLite (PostgreSQL ready)
- **Image Processing:** OpenCV, PIL, pdf2image
- **Validation:** Pydantic
- **API Docs:** Swagger/OpenAPI

### Frontend (To Build)

- **Framework:** Next.js 14+
- **UI:** Shadcn/ui + Tailwind CSS
- **State:** TanStack Query
- **HTTP:** Axios

## 📦 Dependencies

```
fastapi
uvicorn
sqlalchemy
pydantic
python-multipart
pdf2image
opencv-python
pillow
python-dotenv
```

See [requirements.txt](api/requirements.txt) for exact versions.

## 💾 File Organization

Created automatically:

```
uploads/          # Uploaded PDF files
pages/            # Extracted TIFF pages
  └── document_name/
      └── page_0001.tif
lines/            # Extracted line images
  └── document_name/
      └── page_0001/
          ├── line_0001.tif
          └── line_0001.gt.txt
test.db           # SQLite database
```

## 🔍 Example Usage

### Using cURL

```bash
# 1. Upload PDF
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@book.pdf"

# Returns: {"id": "uuid", ...}

# 2. Convert pages
curl -X POST http://localhost:8000/documents/550e8400.../convert-pages

# 3. Extract lines from first page
curl -X POST http://localhost:8000/documents/.../pages/.../extract-lines

# 4. Get unverified lines
curl http://localhost:8000/documents/.../lines?verified=false

# 5. Correct a line
curl -X PUT http://localhost:8000/lines/uuid/corrected-text \
  -H "Content-Type: application/json" \
  -d '{"corrected_text": "නිවැරදි ශබ්ද"}'

# 6. Verify
curl -X PUT http://localhost:8000/lines/uuid/verify

# 7. Export
curl http://localhost:8000/documents/uuid/export -o dataset.zip
```

### Using Python

```python
import requests

BASE = "http://localhost:8000"

# Upload
with open("book.pdf", "rb") as f:
    doc = requests.post(f"{BASE}/documents/upload",
                       files={"file": f}).json()

# Convert
requests.post(f"{BASE}/documents/{doc['id']}/convert-pages")

# Export
requests.get(f"{BASE}/documents/{doc['id']}/export")
```

## 📱 Frontend (Next Steps)

Build a Next.js web app with:

- PDF upload interface
- Page viewer
- Line annotation tool
- Verification dashboard
- Dataset management

See [FRONTEND_GUIDE.md](api/FRONTEND_GUIDE.md) for detailed instructions.

## 🔐 Security Features

- ✅ File upload validation
- ✅ Input validation (Pydantic)
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ CORS configured
- ✅ Error handling
- ✅ Type hints throughout

**To Add:**

- JWT authentication
- Role-based access control
- Rate limiting
- HTTPS enforcement
- Input size limits

## 📊 Features Implemented

✅ PDF upload and processing
✅ Multi-page PDF to TIFF conversion
✅ Line extraction using OpenCV
✅ Ground truth text file management
✅ Text correction and verification workflow
✅ Dataset export (ZIP format)
✅ User management with roles
✅ RESTful API (20+ endpoints)
✅ Interactive API documentation
✅ File serving
✅ Error handling
✅ Database relationships
✅ Timestamps and status tracking

## 🚀 Deployment

### Local Development

```bash
cd api
python -m uvicorn app.main:app --reload
```

### Docker

```bash
docker-compose build
docker-compose up -d
```

### Cloud

- Heroku
- Railway
- Render
- AWS/Azure/GCP

See [DEPLOYMENT.md](api/DEPLOYMENT.md) for details.

## 🧪 Testing

Run included test script:

```bash
python api/test_api.py
```

This tests:

- Health check
- User creation
- Document upload
- PDF conversion
- Line extraction
- Corrections
- Verification
- Export

## 📝 Configuration

Create `.env` file (or use `.env.example` as template):

```env
DATABASE_URL=sqlite:///./test.db
API_PORT=8000
DEBUG=True
MAX_UPLOAD_SIZE=100000000
```

## 📈 Monitoring

- Health check: `GET /health`
- API docs: `http://localhost:8000/docs`
- Logs: Check console output or file

## 🐛 Troubleshooting

### PDF conversion fails

```bash
# Check poppler installation
which pdftoimage  # macOS/Linux
where pdftoimage  # Windows
```

### Port 8000 already in use

```bash
python -m uvicorn app.main:app --port 8001
```

### Database errors

```bash
# Recreate database
rm test.db
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## 🔗 Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [OpenCV Docs](https://docs.opencv.org/)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)

## 📄 License

MIT

## 🤝 Contributing

Contributions welcome! Areas to improve:

- Tesseract OCR integration
- Advanced image preprocessing
- Batch processing
- Performance optimization
- Frontend implementation

## 📞 Support

For issues or questions:

1. Check [README.md](api/README.md)
2. Review [API_ENDPOINTS.md](api/API_ENDPOINTS.md)
3. Run [test_api.py](api/test_api.py)
4. Check logs for errors

---

**Ready to build Tesseract training datasets! 🚀**

Start with:

1. Backend: `cd api && python -m uvicorn app.main:app --reload`
2. API Docs: `http://localhost:8000/docs`
3. Test: `python api/test_api.py`
4. Frontend: Follow [FRONTEND_GUIDE.md](api/FRONTEND_GUIDE.md)
