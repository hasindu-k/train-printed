from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from uuid import UUID
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.models import Document, Page, LineImage, User
from app.schemas import DocumentCreate, DocumentResponse, DocumentUpdate
from app.security import get_current_user, get_current_reviewer
from app.utils import (
    sanitize_filename,
    create_tiff_from_pdf,
    extract_lines_from_page,
    update_gt_text_file,
    read_gt_text_file,
    export_dataset,
    extract_text_from_image,
)

router = APIRouter(prefix="/documents", tags=["documents"])

# Base directory for storing files
BASE_UPLOAD_DIR = "uploads"
PAGES_DIR = "pages"
LINES_DIR = "lines"


def ensure_dirs():
    """Ensure necessary directories exist."""
    os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(PAGES_DIR, exist_ok=True)
    os.makedirs(LINES_DIR, exist_ok=True)


# ============ DOCUMENT MANAGEMENT ============

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📌 1️⃣ Upload & Register Document
    Upload PDF and create document record (Authenticated users)
    """
    ensure_dirs()
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Save uploaded file
        file_path = os.path.join(BASE_UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Extract document name from filename
        doc_name = sanitize_filename(file.filename)

        # if pdf get number of pages
        from app.utils import get_no_of_pages_in_pdf
        num_pages = get_no_of_pages_in_pdf(file_path)
        
        # Create document record
        db_document = Document(
            original_filename=file.filename,
            stored_path=file_path,
            pages_folder=f"{PAGES_DIR}/{doc_name}",
            status="uploaded",
            total_pages=num_pages if num_pages is not None else 0
        )
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return db_document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/", response_model=list[DocumentResponse])
def list_documents(request: Request, db: Session = Depends(get_db)):
    """List all documents with line extraction/verification counts."""
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    if not documents:
        return []

    doc_ids = [doc.id for doc in documents]
    counts = (
        db.query(
            Page.document_id.label("doc_id"),
            func.count(LineImage.id).label("lines_extracted"),
            func.coalesce(
                func.sum(case((LineImage.verified == True, 1), else_=0)), 0
            ).label("lines_verified"),
        )
        .join(LineImage, LineImage.page_id == Page.id)
        .filter(Page.document_id.in_(doc_ids))
        .group_by(Page.document_id)
        .all()
    )

    counts_map = {
        row.doc_id: {
            "lines_extracted": row.lines_extracted,
            "lines_verified": row.lines_verified,
        }
        for row in counts
    }

    # Construct base URL
    base_url = str(request.base_url).rstrip('/')

    return [
        DocumentResponse(
            id=doc.id,
            original_filename=doc.original_filename,
            stored_path=f"{base_url}/{doc.stored_path.replace(os.sep, '/')}",
            status=doc.status,
            total_pages=doc.total_pages,
            lines_extracted=counts_map.get(doc.id, {}).get("lines_extracted", 0),
            lines_verified=counts_map.get(doc.id, {}).get("lines_verified", 0),
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]


# ============ FINALIZED DATASETS ============

@router.get("/finalized-datasets")
def list_finalized_datasets(request: Request, db: Session = Depends(get_db)):
    """
    📌 List All Finalized Datasets
    Get all created finalized datasets with metadata
    
    Returns:
        List of datasets with:
        - id: document_id
        - name: document name
        - documents: number of source documents (always 1 per dataset)
        - totalLines: total verified lines
        - verifiedLines: total verified lines (same as totalLines)
        - createdAt: creation date
        - size: folder size in MB
        - downloadUrl: URL to download zip
    """
    finalized_dir = os.path.join(BASE_UPLOAD_DIR, "finalized")
    
    if not os.path.exists(finalized_dir):
        return []
    
    datasets = []
    
    # Iterate through finalized folders
    for folder_name in os.listdir(finalized_dir):
        folder_path = os.path.join(finalized_dir, folder_name)
        
        if not os.path.isdir(folder_path):
            continue
        
        # Find the corresponding document by name
        document = db.query(Document).filter(
            Document.original_filename.like(f"%{folder_name}%")
        ).first()
        
        if not document:
            # Try to match by sanitized filename
            all_docs = db.query(Document).all()
            for doc in all_docs:
                if sanitize_filename(doc.original_filename) == folder_name:
                    document = doc
                    break
        
        # Count files in the folder
        tif_files = [f for f in os.listdir(folder_path) if f.endswith('.tif')]
        total_lines = len(tif_files)
        
        # Calculate folder size
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                total_size += os.path.getsize(file_path)
        
        size_mb = total_size / (1024 * 1024)  # Convert to MB
        
        # Get creation time
        created_at = datetime.fromtimestamp(os.path.getctime(folder_path))
        
        # Construct base URL
        base_url = str(request.base_url).rstrip('/')
        
        datasets.append({
            "id": str(document.id) if document else folder_name,
            "name": folder_name,
            "documents": 1,
            "totalLines": total_lines,
            "verifiedLines": total_lines,
            "createdAt": created_at.isoformat(),
            "size": f"{size_mb:.1f} MB",
            "downloadUrl": f"{base_url}/documents/finalized-datasets/{folder_name}/download"
        })
    
    # Sort by creation date (newest first)
    datasets.sort(key=lambda x: x["createdAt"], reverse=True)
    
    return datasets


@router.get("/finalized-datasets/{dataset_name}/download")
def download_finalized_dataset(dataset_name: str, db: Session = Depends(get_db)):
    """
    📌 Download Finalized Dataset as ZIP
    Creates and returns a zip file of the finalized dataset
    
    Args:
        dataset_name: Name of the finalized dataset folder
    
    Returns:
        ZIP file download
    """
    finalized_folder = os.path.join(BASE_UPLOAD_DIR, "finalized", dataset_name)
    
    if not os.path.exists(finalized_folder):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finalized dataset not found"
        )
    
    try:
        # Create zip file
        export_dir = os.path.join(BASE_UPLOAD_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)
        output_zip = os.path.join(export_dir, f"{dataset_name}_finalized.zip")
        
        # Use export_dataset utility to create zip
        export_dataset(finalized_folder, output_zip)
        
        # Return the zip file as download
        from fastapi.responses import FileResponse
        return FileResponse(
            path=output_zip,
            filename=f"{dataset_name}_finalized.zip",
            media_type="application/zip"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating zip file: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, request: Request, db: Session = Depends(get_db)):
    """Get a specific document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    counts = (
        db.query(
            func.count(LineImage.id).label("lines_extracted"),
            func.coalesce(
                func.sum(case((LineImage.verified == True, 1), else_=0)), 0
            ).label("lines_verified"),
        )
        .join(Page, Page.id == LineImage.page_id)
        .filter(Page.document_id == document_id)
        .first()
    )

    # Construct base URL
    base_url = str(request.base_url).rstrip('/')

    return DocumentResponse(
        id=document.id,
        original_filename=document.original_filename,
        stored_path=f"{base_url}/{document.stored_path.replace(os.sep, '/')}",
        status=document.status,
        total_pages=document.total_pages,
        lines_extracted=counts.lines_extracted if counts else 0,
        lines_verified=counts.lines_verified if counts else 0,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


@router.put("/{document_id}", response_model=DocumentResponse)
def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Update document metadata."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document_data.status is not None:
        document.status = document_data.status
    if document_data.total_pages is not None:
        document.total_pages = document_data.total_pages
    
    document.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    """Delete a document and all associated files."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Clean up folders
    if document.pages_folder and os.path.exists(document.pages_folder):
        shutil.rmtree(document.pages_folder)
    
    doc_name = sanitize_filename(document.original_filename)
    lines_folder = os.path.join(LINES_DIR, doc_name)
    if os.path.exists(lines_folder):
        shutil.rmtree(lines_folder)
    
    # Delete from database
    db.delete(document)
    db.commit()


# ============ PDF TO TIFF CONVERSION ============

@router.post("/{document_id}/convert-pages", response_model=DocumentResponse)
def convert_pdf_to_pages(document_id: UUID, db: Session = Depends(get_db)):
    """
    📌 2️⃣ Convert PDF → TIFF Pages
    Converts PDF to TIFF pages and creates DB records
    """
    ensure_dirs()
    
    document = db.query(Document).filter(Document.id == document_id).first()

    # check if already processed
    if document and document.status == "processed":
        print("Document already processed, skipping conversion.")
        return document
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.stored_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF file not found"
        )
    
    try:
        document.status = "processing"
        db.commit()
        
        # Convert PDF to TIFF
        pages_folder = document.pages_folder
        num_pages = create_tiff_from_pdf(document.stored_path, pages_folder)
        
        # Create DB records for pages
        for i in range(1, num_pages + 1):
            page_path = f"{pages_folder}/page_{i:04d}.tif"
            db_page = Page(
                document_id=document_id,
                page_number=i,
                tif_path=page_path,
                status="pending"
            )
            db.add(db_page)
        
        document.status = "processed"
        document.total_pages = num_pages
        document.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(document)
        
        return document
    except Exception as e:
        document.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error converting PDF: {str(e)}"
        )


# ============ LIST PAGES ============

@router.get("/{document_id}/pages", response_model=list)
def list_document_pages(document_id: UUID, db: Session = Depends(get_db)):
    """
    📌 3️⃣ List Pages
    Get all pages for a document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    pages = db.query(Page).filter(Page.document_id == document_id).all()
    return pages


# ============ LINE EXTRACTION ============

@router.post("/{document_id}/pages/{page_id}/extract-lines")
def extract_lines_from_page_endpoint(
    document_id: UUID,
    page_id: UUID,
    db: Session = Depends(get_db)
):
    """
    📌 4️⃣ Extract Line Images for a Page
    Extracts lines from a page and creates DB records
    """
    ensure_dirs()
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    page = db.query(Page).filter(
        Page.id == page_id,
        Page.document_id == document_id
    ).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    if not os.path.exists(page.tif_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TIFF file not found"
        )
    
    try:
        # Extract lines
        doc_name = sanitize_filename(document.original_filename)
        page_name = f"page_{page.page_number:04d}"
        output_folder = os.path.join(LINES_DIR, doc_name, page_name)
        
        num_lines = extract_lines_from_page(page.tif_path, output_folder)
        
        # Create DB records for line images
        for i in range(1, num_lines + 1):
            line_path = os.path.join(output_folder, f"line_{i:04d}.tif")
            png_path = os.path.join(output_folder, f"line_{i:04d}.png")
            gt_text_path = os.path.join(output_folder, f"line_{i:04d}.gt.txt")
            
            db_line = LineImage(
                page_id=page_id,
                image_path=line_path,
                png_path=png_path,
                gt_text_path=gt_text_path,
                verified=False
            )
            db.add(db_line)
        
        page.status = "processed"
        page.updated_at = datetime.utcnow()
        db.commit()

        document.status = "extracted"
        db.commit()
        
        return {
            "status": "success",
            "page_id": str(page_id),
            "lines_extracted": num_lines
        }
    except Exception as e:
        page.status = "failed"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting lines: {str(e)}"
        )

@router.post("/{document_id}/extract-lines")
def extract_lines_from_document_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    📌 4️⃣ Extract Line Images for Document (bulk)
    Extracts lines from all pages in a document and creates DB records
    """
    ensure_dirs()
    
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Get all pages for this document
        pages = db.query(Page).filter(Page.document_id == document_id).all()
        
        total_lines_extracted = 0
        for page in pages:
            if not os.path.exists(page.tif_path):
                continue  # skip missing files
            
            # Extract lines
            doc_name = sanitize_filename(document.original_filename)
            page_name = f"page_{page.page_number:04d}"
            output_folder = os.path.join(LINES_DIR, doc_name, page_name)
            
            num_lines = extract_lines_from_page(page.tif_path, output_folder)
            total_lines_extracted += num_lines
            
            # Create DB records for line images
            for i in range(1, num_lines + 1):
                line_path = os.path.join(output_folder, f"line_{i:04d}.tif")
                png_path = os.path.join(output_folder, f"line_{i:04d}.png")
                gt_text_path = os.path.join(output_folder, f"line_{i:04d}.gt.txt")
                
                db_line = LineImage(
                    page_id=page.id,
                    image_path=line_path,
                    png_path=png_path,
                    gt_text_path=gt_text_path,
                    verified=False
                )
                db.add(db_line)
            
            page.status = "processed"
            page.updated_at = datetime.utcnow()
            db.commit()

        # document status update
        document.status = "extracted"
        db.commit()
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "total_lines_extracted": total_lines_extracted
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting lines: {str(e)}"
        )

# ============ OCR TEXT EXTRACTION ============

@router.post("/{document_id}/extract-text")
def extract_text_from_document_lines(
    document_id: UUID,
    lang: str = "sin",
    db: Session = Depends(get_db)
):
    """
    📌 Extract Text from Line Images using Tesseract OCR
    Processes all line images for a document and saves to auto_text column
    
    Args:
        document_id: Document UUID
        lang: Tesseract language (eng, sin, etc.)
    """
    import time
    start_time = time.perf_counter()
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Get all pages for this document
        pages = db.query(Page).filter(Page.document_id == document_id).all()
        
        total_processed = 0
        total_failed = 0
        
        for page in pages:
            # Get all line images for this page
            line_images = db.query(LineImage).filter(LineImage.page_id == page.id).all()
            
            for line_image in line_images:
                if not line_image.image_path or not os.path.exists(line_image.image_path):
                    total_failed += 1
                    continue
                
                try:
                    # Extract text using Tesseract
                    extracted_text = extract_text_from_image(line_image.image_path, lang="sin")
                    
                    # Update auto_text in database
                    line_image.auto_text = extracted_text
                    line_image.updated_at = datetime.utcnow()
                    print(f"Extracted text count yet {total_processed + 1}")
                    total_processed += 1
                    
                except Exception as e:
                    print(f"Failed to extract text from {line_image.image_path}: {str(e)}")
                    total_failed += 1
        
        db.commit()
        elapsed = time.perf_counter() - start_time   # ⏱️ Stop timer
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "total_processed": total_processed,
            "total_failed": total_failed,
            "language": lang,
            "processing_time_seconds": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting text: {str(e)}"
        )


# ============ CREATE GROUND TRUTH TEXT FILES ============

@router.post("/{document_id}/pages/{page_id}/create-gt-files")
def create_gt_files_for_page(
    document_id: UUID,
    page_id: UUID,
    db: Session = Depends(get_db)
):
    """
    📌 5️⃣ Create Ground Truth Text Files (per page)
    Creates empty .gt.txt files for each line image
    """
    page = db.query(Page).filter(
        Page.id == page_id,
        Page.document_id == document_id
    ).first()
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Page not found"
        )
    
    try:
        # Get all line images for this page
        line_images = db.query(LineImage).filter(LineImage.page_id == page_id).all()
        
        created_count = 0
        for line_image in line_images:
            if line_image.gt_text_path:
                os.makedirs(os.path.dirname(line_image.gt_text_path), exist_ok=True)
                if not os.path.exists(line_image.gt_text_path):
                    with open(line_image.gt_text_path, "w", encoding="utf-8") as f:
                        f.write("")
                    created_count += 1
        
        return {
            "status": "success",
            "page_id": str(page_id),
            "gt_files_created": created_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating GT files: {str(e)}"
        )


@router.post("/{document_id}/create-gt-files")
def create_gt_files_for_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    📌 5️⃣ Create Ground Truth Text Files (bulk for document)
    Creates empty .gt.txt files for all line images in document
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        # Get all pages for this document
        pages = db.query(Page).filter(Page.document_id == document_id).all()
        
        total_created = 0
        for page in pages:
            line_images = db.query(LineImage).filter(LineImage.page_id == page.id).all()
            for line_image in line_images:
                if line_image.gt_text_path:
                    os.makedirs(os.path.dirname(line_image.gt_text_path), exist_ok=True)
                    if not os.path.exists(line_image.gt_text_path):
                        with open(line_image.gt_text_path, "w", encoding="utf-8") as f:
                            f.write("")
                        total_created += 1
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "gt_files_created": total_created
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating GT files: {str(e)}"
        )


# ============ FETCH LINES FOR LABELING ============

@router.get("/{document_id}/lines")
def fetch_lines_for_labeling(
    document_id: UUID,
    request: Request,
    verified: bool = None,
    page_num: int = None,
    assigned_to: UUID = None,
    include_invalid: bool = False,
    db: Session = Depends(get_db)
):
    """
    📌 6️⃣ Fetch Lines for Labeling
    Get line images with filtering support
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get all pages for this document
    pages = db.query(Page).filter(Page.document_id == document_id).all()
    page_ids = [p.id for p in pages]
    
    # Query line images
    query = db.query(LineImage).filter(LineImage.page_id.in_(page_ids))

    # Exclude invalid lines by default
    if not include_invalid:
        query = query.filter(LineImage.is_invalid == False)  # noqa: E712
    
    if verified is not None:
        query = query.filter(LineImage.verified == verified)
    
    if page_num is not None:
        page = db.query(Page).filter(
            Page.document_id == document_id,
            Page.page_number == page_num
        ).first()
        if page:
            query = query.filter(LineImage.page_id == page.id)
    
    if assigned_to is not None:
        query = query.filter(LineImage.reviewer_id == assigned_to)
    
    lines = query.all()
    
    # Construct base URL
    base_url = str(request.base_url).rstrip('/')
    
    return [
        {
            "id": str(line.id),
            "page_id": str(line.page_id),
            "page_number": line.page.page_number if line.page else None,
            "image_path": f"{base_url}/{line.png_path.replace(os.sep, '/')}" if line.png_path else None,
            "auto_text": line.auto_text,
            "corrected_text": line.corrected_text,
            "verified": line.verified,
            "is_invalid": line.is_invalid,
            "reviewer_id": str(line.reviewer_id) if line.reviewer_id else None,
        }
        for line in lines
    ]


# ============ EXPORT DATASET ============

@router.get("/{document_id}/export")
def export_document_dataset(document_id: UUID, db: Session = Depends(get_db)):
    """
    📌 🔟 Export Dataset for Training
    Exports all lines and GT files as zip
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        doc_name = sanitize_filename(document.original_filename)
        lines_folder = os.path.join(LINES_DIR, doc_name)
        
        if not os.path.exists(lines_folder):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No line images found for this document"
            )
        
        # Create zip file
        export_dir = os.path.join(BASE_UPLOAD_DIR, "exports")
        os.makedirs(export_dir, exist_ok=True)
        output_zip = os.path.join(export_dir, f"{doc_name}_dataset.zip")
        
        export_dataset(lines_folder, output_zip)
        
        return {
            "status": "success",
            "download_url": f"/downloads/{doc_name}_dataset.zip",
            "file_path": output_zip
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting dataset: {str(e)}"
        )


@router.post("/{document_id}/create-finalized")
def create_finalized_dataset(document_id: UUID, db: Session = Depends(get_db)):
    """
    📌 Create Finalized Dataset
    Creates a finalized folder with verified TIFF files + GT.txt files
    Organized by document and page structure
    
    Returns:
        {
            "status": "success",
            "document_id": str,
            "finalized_path": str,
            "verified_lines_count": int,
            "folder_structure": str
        }
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        ensure_dirs()
        
        # Create finalized folder
        doc_name = sanitize_filename(document.original_filename)
        finalized_base = os.path.join(BASE_UPLOAD_DIR, "finalized", doc_name)
        os.makedirs(finalized_base, exist_ok=True)
        
        # Get all pages for this document
        pages = db.query(Page).filter(Page.document_id == document_id).all()
        
        total_verified = 0
        
        for page in pages:
            # Get verified line images for this page
            verified_lines = db.query(LineImage).filter(
                LineImage.page_id == page.id,
                LineImage.verified == True
            ).all()
            
            # Copy verified files directly to finalized folder
            for line_image in verified_lines:
                if line_image.image_path and os.path.exists(line_image.image_path):
                    # Extract line number from original path
                    original_filename = os.path.basename(line_image.image_path)
                    # Create filename with page prefix: page_0001_line_0046.tif
                    page_prefix = f"page_{page.page_number:04d}_"
                    filename_with_page = page_prefix + original_filename
                    
                    # Copy TIFF file
                    dest_tif = os.path.join(finalized_base, filename_with_page)
                    shutil.copy2(line_image.image_path, dest_tif)
                    
                    # Copy or create GT.txt file
                    if line_image.gt_text_path and os.path.exists(line_image.gt_text_path):
                        gt_filename = filename_with_page.replace('.tif', '.gt.txt')
                        dest_gt = os.path.join(finalized_base, gt_filename)
                        shutil.copy2(line_image.gt_text_path, dest_gt)
                    else:
                        # Create GT.txt file with corrected text if available
                        gt_filename = filename_with_page.replace('.tif', '.gt.txt')
                        dest_gt = os.path.join(finalized_base, gt_filename)
                        with open(dest_gt, 'w', encoding='utf-8') as f:
                            if line_image.corrected_text:
                                f.write(line_image.corrected_text)
                            else:
                                f.write("")
                    
                    total_verified += 1
        
        return {
            "status": "success",
            "document_id": str(document_id),
            "document_name": doc_name,
            "finalized_path": finalized_base,
            "verified_lines_count": total_verified,
            "file_naming": "page_XXXX_line_XXXX.tif + .gt.txt"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating finalized dataset: {str(e)}"
        )



