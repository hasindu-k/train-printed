from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
import os
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.models import LineImage, Page, User
from app.schemas import LineImageCreate, LineImageResponse, LineImageUpdate
from app.security import get_current_user, get_current_reviewer
from app.utils import update_gt_text_file, read_gt_text_file, extract_text_from_image

router = APIRouter(prefix="/api/lines", tags=["lines"])


class LineImageCorrection(BaseModel):
    corrected_text: str


class LineImageVerification(BaseModel):
    reviewer_id: UUID = None
    corrected_text: str = None


# ============ BASIC CRUD ============

@router.post("/", response_model=LineImageResponse, status_code=status.HTTP_201_CREATED)
def create_line_image(line_image: LineImageCreate, db: Session = Depends(get_db)):
    db_line_image = LineImage(
        image_path=line_image.image_path,
        auto_text=line_image.auto_text,
        verified=False
    )
    db.add(db_line_image)
    db.commit()
    db.refresh(db_line_image)
    return db_line_image


@router.get("/{line_image_id}", response_model=dict)
def get_line_image(line_image_id: UUID, db: Session = Depends(get_db)):
    """
    📌 7️⃣ Get Line Image + Text
    Get line image with all metadata and paths
    """
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    
    # Read GT text content
    gt_text_content = ""
    if line_image.gt_text_path and os.path.exists(line_image.gt_text_path):
        gt_text_content = read_gt_text_file(line_image.gt_text_path)
    
    return {
        "id": str(line_image.id),
        "page_id": str(line_image.page_id),
        "image_path": line_image.image_path,
        "image_url": f"/images/{line_image.image_path}",
        "gt_text_path": line_image.gt_text_path,
        "auto_text": line_image.auto_text,
        "corrected_text": line_image.corrected_text,
        "gt_text_content": gt_text_content,
        "verified": line_image.verified,
        "reviewer_id": str(line_image.reviewer_id) if line_image.reviewer_id else None,
        "created_at": line_image.created_at.isoformat(),
        "updated_at": line_image.updated_at.isoformat()
    }


@router.put("/{line_image_id}", response_model=LineImageResponse)
def update_line_image(
    line_image_id: UUID,
    line_image_data: LineImageUpdate,
    db: Session = Depends(get_db)
):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    
    if line_image_data.corrected_text is not None:
        line_image.corrected_text = line_image_data.corrected_text
    if line_image_data.verified is not None:
        line_image.verified = line_image_data.verified
    if line_image_data.reviewer_id is not None:
        line_image.reviewer_id = line_image_data.reviewer_id
    
    line_image.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(line_image)
    return line_image


@router.delete("/{line_image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_image(line_image_id: UUID, db: Session = Depends(get_db)):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    db.delete(line_image)
    db.commit()


# ============ CORRECTION ENDPOINTS ============

@router.put("/{line_image_id}/corrected-text")
def save_corrected_text(
    line_image_id: UUID,
    correction: LineImageCorrection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    📌 8️⃣ Save Corrected GT Text
    Update corrected text and .gt.txt file on disk (Authenticated users)
    """
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    
    try:
        # Update database
        line_image.corrected_text = correction.corrected_text
        line_image.updated_at = datetime.utcnow()
        
        # Update .gt.txt file on disk (without overwriting auto_text)
        if line_image.gt_text_path:
            update_gt_text_file(line_image.gt_text_path, correction.corrected_text)
        
        db.commit()
        db.refresh(line_image)
        
        return {
            "status": "success",
            "line_id": str(line_image_id),
            "corrected_text": correction.corrected_text,
            "gt_file_updated": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving correction: {str(e)}"
        )


# ============ VERIFICATION ENDPOINTS ============

@router.put("/{line_image_id}/verify")
def verify_line(
    line_image_id: UUID,
    current_user: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db),
    verification: LineImageVerification = LineImageVerification()
):
    """
    📌 9️⃣ Verify Line
    Mark a line as verified (Reviewer or Admin only)
    Optionally update corrected text and GT.txt file
    """
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    

    try:
        # Update corrected text if provided
        if verification.corrected_text is not None:
            line_image.corrected_text = verification.corrected_text
            
            # Update .gt.txt file on disk
            if line_image.gt_text_path:
                update_gt_text_file(line_image.gt_text_path, verification.corrected_text)
        
        line_image.verified = True
        # Set reviewer to current user if not specified
        line_image.reviewer_id = verification.reviewer_id if verification.reviewer_id else current_user.id
        
        line_image.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(line_image)
        
        return {
            "status": "success",
            "line_id": str(line_image_id),
            "verified": True
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verifying line: {str(e)}"
        )


@router.put("/{line_image_id}/unverify")
def unverify_line(
    line_image_id: UUID,
    current_user: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db)
):
    """
    📌 9️⃣ Unverify Line
    Undo verification of a line (Reviewer or Admin only)
    """
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    
    line_image.verified = False
    line_image.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(line_image)
    
    return {
        "status": "success",
        "line_id": str(line_image_id),
        "verified": False
    }


# ============ IMAGE SERVING ============

@router.get("/{line_image_id}/image")
def get_line_image_file(line_image_id: UUID, db: Session = Depends(get_db)):
    """Serve the line image file."""
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image or not os.path.exists(line_image.image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image file not found"
        )
    
    return FileResponse(line_image.image_path, media_type="image/tiff")


# ============ BULK OPERATIONS ============

@router.get("/page/{page_id}/all")
def get_page_lines(page_id: UUID, db: Session = Depends(get_db)):
    """Get all lines for a specific page."""
    lines = db.query(LineImage).filter(LineImage.page_id == page_id).all()
    return [
        {
            "id": str(line.id),
            "page_id": str(line.page_id),
            "image_path": line.image_path,
            "auto_text": line.auto_text,
            "corrected_text": line.corrected_text,
            "verified": line.verified,
        }
        for line in lines
    ]


# ============ TEXT EXTRACTION ============

@router.post("/{line_image_id}/extract-text")
def extract_text(
    line_image_id: UUID,
    lang: str = "sin",
    db: Session = Depends(get_db)
):
    """
    Extract text from a single line image using Tesseract OCR.
    Processes the line image and saves to auto_text column.
    
    Args:
        line_image_id: LineImage UUID
        lang: Tesseract language (eng, sin, etc.)
    """
    import time
    start_time = time.perf_counter()
    
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    
    if not line_image.image_path or not os.path.exists(line_image.image_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file not found"
        )
    
    try:
        # Extract text using Tesseract
        extracted_text = extract_text_from_image(line_image.image_path, lang=lang)
        
        # Update auto_text in database
        line_image.auto_text = extracted_text
        line_image.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(line_image)
        
        elapsed = time.perf_counter() - start_time
        
        return {
            "status": "success",
            "line_image_id": str(line_image_id),
            "extracted_text": extracted_text,
            "language": lang,
            "processing_time_seconds": round(elapsed, 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting text: {str(e)}"
        )
