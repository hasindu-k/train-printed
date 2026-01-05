from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
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
def list_documents(db: Session = Depends(get_db)):
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

    return [
        DocumentResponse(
            id=doc.id,
            original_filename=doc.original_filename,
            stored_path=doc.stored_path,
            status=doc.status,
            total_pages=doc.total_pages,
            lines_extracted=counts_map.get(doc.id, {}).get("lines_extracted", 0),
            lines_verified=counts_map.get(doc.id, {}).get("lines_verified", 0),
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )
        for doc in documents
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID, db: Session = Depends(get_db)):
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

    return DocumentResponse(
        id=document.id,
        original_filename=document.original_filename,
        stored_path=document.stored_path,
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
            gt_text_path = os.path.join(output_folder, f"line_{i:04d}.gt.txt")
            
            db_line = LineImage(
                page_id=page_id,
                image_path=line_path,
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
                gt_text_path = os.path.join(output_folder, f"line_{i:04d}.gt.txt")
                
                db_line = LineImage(
                    page_id=page.id,
                    image_path=line_path,
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
    verified: bool = None,
    page_num: int = None,
    assigned_to: UUID = None,
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
    return [
        {
            "id": str(line.id),
            "page_id": str(line.page_id),
            "image_path": line.image_path,
            "auto_text": line.auto_text,
            "corrected_text": line.corrected_text,
            "verified": line.verified,
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
