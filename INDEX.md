# Project Files Index

## 📁 Backend API Files

### Core Application

- **[api/app/main.py](api/app/main.py)** - FastAPI application setup, routing, CORS, static files
- **[api/app/database.py](api/app/database.py)** - SQLAlchemy database configuration & session management
- **[api/app/utils.py](api/app/utils.py)** - Image processing utilities (PDF→TIFF, line extraction, GT files)

### Database Models

- **[api/app/models/**init**.py](api/app/models/__init__.py)** - 4 SQLAlchemy ORM models:
  - User (admin, reviewer, annotator roles)
  - Document (PDFs with status tracking)
  - Page (TIFF pages extracted from PDFs)
  - LineImage (Text lines with correction capability)

### Request/Response Schemas

- **[api/app/schemas/**init**.py](api/app/schemas/__init__.py)** - 8 Pydantic schemas:
  - UserCreate, UserResponse
  - DocumentCreate, DocumentUpdate, DocumentResponse
  - PageCreate, PageUpdate, PageResponse
  - LineImageCreate, LineImageUpdate, LineImageResponse
  - LineImageCorrection, LineImageVerification

### API Routes

- **[api/app/routes/users.py](api/app/routes/users.py)** - User management endpoints
- **[api/app/routes/documents.py](api/app/routes/documents.py)** - Document workflow (upload, convert, extract, export)
- **[api/app/routes/pages.py](api/app/routes/pages.py)** - Page management
- **[api/app/routes/line_images.py](api/app/routes/line_images.py)** - Line correction & verification

### Configuration & Dependencies

- **[api/requirements.txt](api/requirements.txt)** - Python package dependencies
- **[api/.env.example](api/.env.example)** - Environment variables template

## 📚 Documentation

### Backend Documentation

- **[api/README.md](api/README.md)** ⭐ - Complete API setup, usage guide, and examples
- **[api/QUICKSTART.md](api/QUICKSTART.md)** - Quick start guide for developers
- **[api/API_ENDPOINTS.md](api/API_ENDPOINTS.md)** - Reference for all 20+ API endpoints
- **[api/SUMMARY.md](api/SUMMARY.md)** - Implementation summary and features overview

### Deployment & Production

- **[api/DEPLOYMENT.md](api/DEPLOYMENT.md)** - Docker, cloud deployment, production setup, monitoring

### Frontend Development

- **[api/FRONTEND_GUIDE.md](api/FRONTEND_GUIDE.md)** - Next.js integration, example code, API client setup

### Main Documentation

- **[README.md](README.md)** - Project overview, quick start, workflow description

## 🧪 Testing & Examples

- **[api/test_api.py](api/test_api.py)** - Comprehensive API endpoint testing script with examples

## 🐍 Existing Python Scripts (Integration Ready)

- **[create_gt_text_files.py](create_gt_text_files.py)** - Creates empty .gt.txt files
- **[pdf_to_tif.py](pdf_to_tif.py)** - Converts PDF to TIFF pages (300 DPI)
- **[seperate_lines.py](seperate_lines.py)** - Extracts line images from pages using OpenCV

---

## 📋 Complete File Structure

```
train-printed/
├── api/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app
│   │   ├── database.py                  # SQLAlchemy config
│   │   ├── utils.py                     # Image processing
│   │   ├── models/
│   │   │   └── __init__.py              # ORM models (4 tables)
│   │   ├── schemas/
│   │   │   └── __init__.py              # Pydantic schemas (8+)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── users.py                 # User endpoints (5)
│   │       ├── documents.py             # Document endpoints (8)
│   │       ├── pages.py                 # Page endpoints (5)
│   │       └── line_images.py           # Line endpoints (8)
│   ├── requirements.txt                 # Dependencies
│   ├── .env.example                     # Config template
│   ├── test_api.py                      # API testing
│   ├── README.md                        # Complete docs
│   ├── QUICKSTART.md                    # Quick start
│   ├── API_ENDPOINTS.md                 # All endpoints
│   ├── SUMMARY.md                       # Implementation summary
│   ├── DEPLOYMENT.md                    # Production guide
│   └── FRONTEND_GUIDE.md                # Next.js guide
├── create_gt_text_files.py              # GT file creator
├── pdf_to_tif.py                        # PDF converter
├── seperate_lines.py                    # Line extractor
└── README.md                            # Project overview
```

---

## 🎯 Key Files to Review First

1. **[api/README.md](api/README.md)** - Start here for complete backend documentation
2. **[api/QUICKSTART.md](api/QUICKSTART.md)** - Quick setup guide
3. **[api/API_ENDPOINTS.md](api/API_ENDPOINTS.md)** - Understanding all endpoints
4. **[api/test_api.py](api/test_api.py)** - Running examples
5. **[README.md](README.md)** - Project overview

---

## 📊 Implementation Statistics

### Code Files

- **Python Files:** 12 (main, utils, models, schemas, routes)
- **Documentation:** 7 markdown files
- **Testing:** 1 comprehensive test script
- **Configuration:** 2 config files

### API Coverage

- **Endpoints:** 26+ total
- **Database Tables:** 4 with relationships
- **Request/Response Models:** 15+ Pydantic schemas
- **Status Codes:** Proper HTTP status codes for all scenarios

### Lines of Code (Estimates)

- **Backend Logic:** ~2,500 lines
- **Documentation:** ~2,000 lines
- **Tests:** ~400 lines

---

## 🚀 Quick Navigation

### To Start Backend

```bash
cd api
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### To Test API

```bash
python api/test_api.py
```

### To Read Documentation

1. Backend: Open `api/README.md`
2. Endpoints: Open `api/API_ENDPOINTS.md`
3. Deploy: Open `api/DEPLOYMENT.md`
4. Frontend: Open `api/FRONTEND_GUIDE.md`

### To Understand Code

- Models: `api/app/models/__init__.py`
- Schemas: `api/app/schemas/__init__.py`
- Routes: `api/app/routes/`
- Utils: `api/app/utils.py`

---

## 📌 Important Notes

### What's Implemented ✅

- Complete PDF to TIFF workflow
- Line extraction from pages
- Ground truth text file management
- Text correction and verification
- User management with roles
- Dataset export as ZIP
- 26+ REST API endpoints
- Full API documentation
- Database with relationships

### What You Can Do Now

1. Upload PDFs
2. Extract TIFF pages
3. Extract line images
4. Create/update ground truth text
5. Verify corrections
6. Filter and search lines
7. Export training datasets
8. Manage users and roles

### What's Next

1. Build Next.js frontend (see FRONTEND_GUIDE.md)
2. Add JWT authentication
3. Deploy to cloud (Docker support ready)
4. Add Tesseract OCR integration
5. Implement batch processing

---

## 🔗 External Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Pydantic Docs](https://docs.pydantic.dev/)
- [OpenCV Docs](https://docs.opencv.org/)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)

---

## 📞 Getting Help

1. **API Issues:** Check `api/README.md` Troubleshooting section
2. **Endpoint Usage:** See `api/API_ENDPOINTS.md`
3. **Testing:** Run `api/test_api.py`
4. **Frontend Setup:** See `api/FRONTEND_GUIDE.md`
5. **Production:** See `api/DEPLOYMENT.md`

---

**Everything is ready to use! Start with [api/README.md](api/README.md) 🚀**
