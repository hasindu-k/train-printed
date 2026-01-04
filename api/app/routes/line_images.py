from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models import LineImage, Page
from app.schemas import LineImageCreate, LineImageResponse, LineImageUpdate

router = APIRouter(prefix="/line-images", tags=["line-images"])


@router.post("/", response_model=LineImageResponse, status_code=status.HTTP_201_CREATED)
def create_line_image(page_id: UUID, line_image: LineImageCreate, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    
    db_line_image = LineImage(
        page_id=page_id,
        image_path=line_image.image_path,
        auto_text=line_image.auto_text,
        verified=False
    )
    db.add(db_line_image)
    db.commit()
    db.refresh(db_line_image)
    return db_line_image


@router.get("/", response_model=list[LineImageResponse])
def list_line_images(page_id: UUID = None, db: Session = Depends(get_db)):
    query = db.query(LineImage)
    if page_id:
        query = query.filter(LineImage.page_id == page_id)
    return query.all()


@router.get("/{line_image_id}", response_model=LineImageResponse)
def get_line_image(line_image_id: UUID, db: Session = Depends(get_db)):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line image not found")
    return line_image


@router.put("/{line_image_id}", response_model=LineImageResponse)
def update_line_image(line_image_id: UUID, line_image_data: LineImageUpdate, db: Session = Depends(get_db)):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line image not found")
    
    if line_image_data.corrected_text is not None:
        line_image.corrected_text = line_image_data.corrected_text
    if line_image_data.verified is not None:
        line_image.verified = line_image_data.verified
    if line_image_data.reviewer_id is not None:
        line_image.reviewer_id = line_image_data.reviewer_id
    
    db.commit()
    db.refresh(line_image)
    return line_image


@router.delete("/{line_image_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line_image(line_image_id: UUID, db: Session = Depends(get_db)):
    line_image = db.query(LineImage).filter(LineImage.id == line_image_id).first()
    if not line_image:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Line image not found")
    db.delete(line_image)
    db.commit()
