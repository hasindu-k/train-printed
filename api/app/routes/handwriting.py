from typing import List, Optional
from fastapi import APIRouter, Form, HTTPException, status, Depends, File, UploadFile, Request, Response
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
import os
import random
import asyncio
from datetime import datetime
from pathlib import Path

from app.database import get_db
from app.models import Document, Page, LineImage, User
from app.schemas import LineImageResponse, LineImageUpdate
from app.security import get_optional_current_user
from app.utils import extract_text_from_image, get_base_url, clean_sinhala_text, optimize_image

router = APIRouter(prefix="/handwriting", tags=["handwriting"])

# Base directory for storing files
BASE_UPLOAD_DIR = "uploads"
PAGES_DIR = "pages"
LINES_DIR = "lines"
HANDWRITING_DIR = "handwriting"

# Path to corpus files
CORPUS_TIER1_PATH = "corpus-tier-1.txt"
CORPUS_TIER2_PATH = "corpus-tier-2.txt"


def ensure_dirs():
    """Ensure necessary directories exist."""
    os.makedirs(BASE_UPLOAD_DIR, exist_ok=True)
    os.makedirs(PAGES_DIR, exist_ok=True)
    os.makedirs(LINES_DIR, exist_ok=True)
    os.makedirs(HANDWRITING_DIR, exist_ok=True)


def get_guest_user_id(
    request: Request,
    response: Response,
    db: Session
) -> UUID:
    """
    Get or create guest user based on cookie.
    
    First request (no cookie): Generate guest_id, create guest user, set cookie
    Next requests: Read guest_id from cookie, return existing user
    """
    guest_id = request.cookies.get("guest_id")

    if guest_id:
        user = db.query(User).filter(User.email == f"guest-{guest_id}@handwriting.local").first()
        if user:
            return user.id

    # Create new guest
    new_guest_id = str(uuid4())

    # Assign a sequential guest number: Guest 1, Guest 2, ...
    guest_count = db.query(User).filter(User.role == "guest").count()
    guest_number = guest_count + 1
    guest_name = f"Guest {guest_number}"

    guest = User(
        name=guest_name,
        email=f"guest-{new_guest_id}@handwriting.local",
        hashed_password="",
        role="guest",
        is_active=True
    )

    db.add(guest)
    db.commit()
    db.refresh(guest)

    response.set_cookie(
        key="guest_id",
        value=new_guest_id,
        httponly=True,
        max_age=60 * 60 * 24 * 30,  # 30 days
        samesite="lax"
    )

    return guest.id


def load_corpus(tier: str = "tier-1") -> List[str]:
    """Load corpus sentences from file."""
    if tier == "tier-1":
        filepath = CORPUS_TIER1_PATH
    elif tier == "tier-2":
        filepath = CORPUS_TIER2_PATH
    else:
        raise ValueError("Invalid tier. Use 'tier-1' or 'tier-2'")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Corpus file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        sentences = [line.strip() for line in f.readlines() if line.strip()]
    
    return sentences


def get_or_create_handwriting_document(db: Session, user_id: UUID, tier: str = "tier-1") -> UUID:
    """Get or create a single handwriting document for the user."""
    # Check if user already has a handwriting document for this tier
    doc = db.query(Document).filter(
        Document.uploaded_by == user_id,
        Document.document_type == f"handwriting-{tier}"
    ).first()
    
    if doc:
        return doc.id
    
    # Fetch user to build a friendly document title
    user = db.query(User).filter(User.id == user_id).first()
    display_name = (user.name if user and user.name else "Guest").strip()
    doc_title = f"Handwriting - {display_name}"

    # Create a new handwriting document
    ensure_dirs()
    doc_name = f"handwriting-{tier}-{user_id}"
    
    new_doc = Document(
        name=doc_title,
        original_filename=doc_title,
        stored_path=f"{HANDWRITING_DIR}/",
        pages_folder=f"{PAGES_DIR}/{doc_name}/",
        status="processed",
        total_pages=1,
        document_type=f"handwriting-{tier}",
        uploaded_by=user_id
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    # Create a virtual page
    page = Page(
        document_id=new_doc.id,
        page_number=1,
        tif_path=f"{PAGES_DIR}/{doc_name}/page_0001.tif",
        status="processed"
    )
    
    db.add(page)
    db.commit()
    db.refresh(page)
    
    return new_doc.id


# ============ HANDWRITING ENDPOINTS ============

@router.get("/corpus")
async def get_corpus_sentences(
    limit: int = 10
):
    """
    Get handwriting practice sentences.
    Always returns 60% tier-1 and 40% tier-2 sentences.
    No authentication required.
    """

    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be greater than 0"
        )

    try:
        # Load both corpora
        tier1_sentences = load_corpus("tier-1")
        tier2_sentences = load_corpus("tier-2")

        # Calculate split
        tier1_count = round(limit * 0.6)
        tier2_count = limit - tier1_count  # ensures total == limit

        # Sample safely
        selected_tier1 = random.sample(
            tier1_sentences,
            min(tier1_count, len(tier1_sentences))
        )

        selected_tier2 = random.sample(
            tier2_sentences,
            min(tier2_count, len(tier2_sentences))
        )

        # Combine & shuffle so tiers are mixed
        combined = selected_tier1 + selected_tier2
        random.shuffle(combined)

        return {
            "requested_limit": limit,
            "distribution": {
                "tier-1": len(selected_tier1),
                "tier-2": len(selected_tier2),
            },
            "sentences": combined
        }

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/submit")
async def submit_handwriting(
    request: Request,
    response: Response,
    tier: str = Form("tier-1"),
    sentence: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    """
    Submit handwritten image for a sentence.
    Can be used by authenticated or guest users.
    No authentication required - guest users automatically get a cookie-based identity.
    
    Args:
        tier: "tier-1" or "tier-2"
        sentence: The sentence text that was written
        file: The handwritten image file
    """
    ensure_dirs()

    if tier not in ["tier-1", "tier-2"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier"
        )
    
    # Determine user (authenticated user or guest)
    if current_user:
        user_id = current_user.id
    else:
        user_id = get_guest_user_id(request, response, db)
    
    try:
        # Get or create handwriting document
        doc_id = get_or_create_handwriting_document(db, user_id, tier)
        
        # Get the document and its first page
        document = db.query(Document).filter(Document.id == doc_id).first()
        page = db.query(Page).filter(Page.document_id == doc_id).first()
        
        # Save uploaded file
        file_ext = file.filename.split(".")[-1].lower()
        if file_ext not in ["png", "jpg", "jpeg", "webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only PNG, JPG, JPEG, WEBP allowed"
            )
        
        # Create directory for line images if not exists
        doc_name = document.pages_folder.split("/")[-2]
        lines_dir = os.path.join(LINES_DIR, doc_name)
        os.makedirs(lines_dir, exist_ok=True)
        
        # Generate unique filename
        line_number = len(db.query(LineImage).filter(LineImage.page_id == page.id).all()) + 1
        filename = f"line_{str(line_number).zfill(4)}.{file_ext}"
        image_path = os.path.join(lines_dir, filename)

        cleaned_sentence = clean_sinhala_text(sentence) if sentence else ""

        print("Saving handwriting submission...")
        print(cleaned_sentence)

        # Save file synchronously (file operations are blocking)
        content = await file.read()
        
        def save_files():
            # Save optimized image
            optimize_image(content, image_path, file_ext)

            # Create gt.txt file with the sentence
            gt_filename = filename.replace(f".{file_ext}", ".gt.txt")
            gt_path = os.path.join(lines_dir, gt_filename)
            with open(gt_path, "w", encoding="utf-8") as f:
                f.write(cleaned_sentence)
            
            return gt_path
        
        # Run file operations in thread pool to not block async
        loop = asyncio.get_event_loop()
        gt_path = await loop.run_in_executor(None, save_files)
        
        # Create line image record
        line_image = LineImage(
            page_id=page.id,
            image_path=image_path,
            png_path=image_path,  # Same for now, can be converted later
            gt_text_path=gt_path,
            auto_text=cleaned_sentence,
            corrected_text=cleaned_sentence,
            verified=False,
            is_invalid=False
        )
        
        db.add(line_image)
        db.commit()
        db.refresh(line_image)
        
        return {
            "status": "success",
            "line_id": str(line_image.id),
            "document_id": str(doc_id),
            "message": "Handwriting submitted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submission failed: {str(e)}"
        )


@router.get("/document/{user_id}/{tier}", response_model=dict)
async def get_handwriting_document(
    user_id: UUID,
    tier: str = "tier-1",
    db: Session = Depends(get_db)
):
    """
    Get handwriting document with all submitted images for a user.
    Shows as a single document from a single user.
    """
    if tier not in ["tier-1", "tier-2"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tier"
        )
    
    try:
        # Get the handwriting document
        document = db.query(Document).filter(
            Document.uploaded_by == user_id,
            Document.document_type == f"handwriting-{tier}"
        ).first()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No handwriting document found for this user"
            )
        
        # Get all pages and line images
        pages = db.query(Page).filter(Page.document_id == document.id).all()
        
        line_images_data = []
        for page in pages:
            line_images = db.query(LineImage).filter(LineImage.page_id == page.id).all()
            for line in line_images:
                line_images_data.append({
                    "id": str(line.id),
                    "image_path": line.image_path,
                    "png_path": line.png_path,
                    "text": line.corrected_text or line.auto_text,
                    "verified": line.verified,
                    "created_at": line.created_at.isoformat()
                })
        
        return {
            "document_id": str(document.id),
            "user_id": str(user_id),
            "tier": tier,
            "title": document.original_filename,
            "total_submissions": len(line_images_data),
            "created_at": document.created_at.isoformat(),
            "line_images": line_images_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.get("/submissions/{document_id}", response_model=List[LineImageResponse])
async def get_document_submissions(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all line image submissions for a handwriting document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    pages = db.query(Page).filter(Page.document_id == document_id).all()
    line_images = []
    
    for page in pages:
        lines = db.query(LineImage).filter(LineImage.page_id == page.id).all()
        line_images.extend(lines)
    
    return line_images