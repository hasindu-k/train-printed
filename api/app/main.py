from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.database import Base, engine
from app.routes import auth, users, documents, pages, line_images, dashboard, handwriting

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document OCR & Tesseract Training API",
    description="API for document processing, OCR, and Tesseract training dataset management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static file directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("pages", exist_ok=True)
os.makedirs("lines", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/pages", StaticFiles(directory="pages"), name="pages")
app.mount("/lines", StaticFiles(directory="lines"), name="lines")

# Include routes
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(pages.router)
app.include_router(line_images.router)
app.include_router(dashboard.router)
app.include_router(handwriting.router)


@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Document OCR & Tesseract Training API",
        "version": "1.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }



@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
