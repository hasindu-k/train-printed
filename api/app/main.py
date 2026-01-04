from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes import users, documents, pages, line_images

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Document OCR API",
    description="API for document processing and OCR",
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

# Include routes
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(pages.router)
app.include_router(line_images.router)


@app.get("/", tags=["root"])
def read_root():
    return {
        "message": "Document OCR API",
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
