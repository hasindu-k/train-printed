from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str = "annotator"  # admin, reviewer, annotator (default: annotator)


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


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
    lines_extracted: int = 0
    lines_verified: int = 0
    document_type: str
    uploaded_by: UUID
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
    is_invalid: Optional[bool] = None


class LineImageResponse(BaseModel):
    id: UUID
    page_id: UUID
    image_path: str
    png_path: Optional[str] = None
    auto_text: Optional[str]
    corrected_text: Optional[str]
    verified: bool
    is_invalid: bool
    reviewer_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserActivityResponse(BaseModel):
    id: UUID
    name: str
    email: str
    role: str
    status: str  # "active" or "inactive"
    linesAnnotated: int
    linesVerified: int
    lastActive: Optional[datetime]

    class Config:
        from_attributes = True