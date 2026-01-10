from fastapi import APIRouter, Depends, File, HTTPException, status, Query, UploadFile
from fastapi.params import Form
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
from app.utils import convert_png_to_tiff, generate_line_variant_paths, update_gt_text_file, read_gt_text_file, extract_text_from_image

router = APIRouter(prefix="/api/lines", tags=["lines"])


class LineImageCorrection(BaseModel):
    corrected_text: str


class LineImageVerification(BaseModel):
    reviewer_id: UUID | None = None
    corrected_text: str | None = None


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
        "is_invalid": line_image.is_invalid,
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
    if line_image_data.is_invalid is not None:
        line_image.is_invalid = line_image_data.is_invalid
    
    line_image.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(line_image)
    return line_image


@router.delete("/{line_image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_image(
    line_image_id: UUID,
    hard: bool = Query(False, description="If true, permanently delete DB row and files. Default marks as invalid."),
    db: Session = Depends(get_db)
):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line image not found"
        )
    # Soft delete by default: mark invalid
    if not hard:
        line_image.is_invalid = True
        line_image.updated_at = datetime.utcnow()
        db.commit()
        return
    # Hard delete: remove files and delete row
    try:
        for p in [line_image.image_path, getattr(line_image, "png_path", None), line_image.gt_text_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        db.delete(line_image)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete line image: {str(e)}")


# ============ INVALIDATION ENDPOINTS ============

@router.put("/{line_image_id}/invalidate")
def invalidate_line(
    line_image_id: UUID,
    current_user: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db)
):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(status_code=404, detail="Line image not found")
    line_image.is_invalid = True
    line_image.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "line_id": str(line_image_id), "is_invalid": True}


@router.put("/{line_image_id}/restore")
def restore_line(
    line_image_id: UUID,
    current_user: User = Depends(get_current_reviewer),
    db: Session = Depends(get_db)
):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(status_code=404, detail="Line image not found")
    line_image.is_invalid = False
    line_image.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "line_id": str(line_image_id), "is_invalid": False}


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

@router.post("/{line_id}/images")
def add_line_image(
    line_id: UUID,
    image_path: str = Form(...),
    page_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    BASE_DIR = "C:/github/train-printed/api/"  # or wherever your lines folder is

    relative_path = image_path.replace("http://localhost:8000/", "")
    full_path = os.path.join(BASE_DIR, relative_path)
    print(f"Uploading line image for line ID {line_id} to path: {full_path}")
    paths = generate_line_variant_paths(full_path)
    print(f"Generated paths: {paths}")

    # Ensure directory exists
    os.makedirs(os.path.dirname(paths["png_path"]), exist_ok=True)

    # Save PNG
    with open(paths["png_path"], "wb") as buffer:
        buffer.write(file.file.read())

    # Create empty GT file
    open(paths["gt_text_path"], "w").close()

    convert_png_to_tiff(paths["png_path"], paths["line_path"])

    # Save DB record
    db_line = LineImage(
        page_id=page_id,
       image_path=os.path.relpath(paths["line_path"], BASE_DIR).replace("/", "\\"),
        png_path=os.path.relpath(paths["png_path"], BASE_DIR).replace("/", "\\"),
        gt_text_path=os.path.relpath(paths["gt_text_path"], BASE_DIR).replace("/", "\\"),
        verified=False,
        created_at=datetime.utcnow()
    )

    print(f"Creating LineImage DB record for line ID {line_id} with paths: {paths}")

    db.add(db_line)
    db.commit()
    db.refresh(db_line)

    # send full url for image_url
    full_image_url = f"http://localhost:8000/{db_line.png_path.replace('\\', '/')}"

    return {
        "status": "success",
        "line_id": str(db_line.id),
        "image_url": full_image_url,
        "paths": paths
    }


# ============ BULK OPERATIONS ============

@router.get("/page/{page_id}/all")
def get_page_lines(page_id: UUID, include_invalid: bool = False, db: Session = Depends(get_db)):
    """Get all lines for a specific page."""
    query = db.query(LineImage).filter(LineImage.page_id == page_id)
    if not include_invalid:
        query = query.filter(LineImage.is_invalid == False)  # noqa: E712
    lines = query.all()
    return [
        {
            "id": str(line.id),
            "page_id": str(line.page_id),
            "image_path": line.image_path,
            "auto_text": line.auto_text,
            "corrected_text": line.corrected_text,
            "verified": line.verified,
            "is_invalid": line.is_invalid,
        }
        for line in lines
    ]


# ============ TEXT EXTRACTION ============

@router.post("/{line_image_id}/extract-text")
def extract_text(
    line_image_id: UUID,
    lang: str = "sin_eng_custom",
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
        extracted_text = extract_text_from_image(line_image.image_path, lang=lang, config="--psm 7")
        
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
