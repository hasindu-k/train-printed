from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models import Page, Document
from app.schemas import PageCreate, PageResponse, PageUpdate

router = APIRouter(prefix="/pages", tags=["pages"])


@router.post("/", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
def create_page(document_id: UUID, page: PageCreate, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    db_page = Page(
        document_id=document_id,
        page_number=page.page_number,
        tif_path=page.tif_path,
        status="pending"
    )
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page


@router.get("/", response_model=list[PageResponse])
def list_pages(document_id: UUID = None, db: Session = Depends(get_db)):
    query = db.query(Page)
    if document_id:
        query = query.filter(Page.document_id == document_id)
    return query.all()


@router.get("/{page_id}", response_model=PageResponse)
def get_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    return page


@router.put("/{page_id}", response_model=PageResponse)
def update_page(page_id: UUID, page_data: PageUpdate, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    
    if page_data.status is not None:
        page.status = page_data.status
    
    db.commit()
    db.refresh(page)
    return page


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page(page_id: UUID, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found")
    db.delete(page)
    db.commit()
