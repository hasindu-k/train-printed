from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str  # admin, reviewer, annotator


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    original_filename: str
    stored_path: str


class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    total_pages: Optional[int] = None


class DocumentResponse(BaseModel):
    id: UUID
    original_filename: str
    stored_path: str
    status: str
    total_pages: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PageCreate(BaseModel):
    page_number: int
    tif_path: str


class PageUpdate(BaseModel):
    status: Optional[str] = None


class PageResponse(BaseModel):
    id: UUID
    document_id: UUID
    page_number: int
    tif_path: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LineImageCreate(BaseModel):
    image_path: str
    auto_text: Optional[str] = None


class LineImageUpdate(BaseModel):
    corrected_text: Optional[str] = None
    verified: Optional[bool] = None
    reviewer_id: Optional[UUID] = None


class LineImageResponse(BaseModel):
    id: UUID
    page_id: UUID
    image_path: str
    auto_text: Optional[str]
    corrected_text: Optional[str]
    verified: bool
    reviewer_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
