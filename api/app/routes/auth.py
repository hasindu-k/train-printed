"""Authentication routes for login and token management."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    get_current_user,
    cleanup_expired_tokens,
)
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    """Login request with email and password."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse


class RegisterRequest(BaseModel):
    """Registration request."""
    name: str
    email: str
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Default role is 'annotator'. Admins should be created by existing admins.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with annotator role by default
    hashed_password = hash_password(request.password)
    new_user = User(
        name=request.name,
        email=request.email,
        hashed_password=hashed_password,
        role="annotator",  # Default role for new users
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(new_user.id), "email": new_user.email})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id), "email": new_user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": new_user
    }


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    Returns access token, refresh token, and user information.
    Cleans up expired tokens from blacklist on each login.
    """
    # Clean up expired tokens from blacklist
    cleanup_expired_tokens(db)
    
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh an expired access token using a refresh token.
    
    Returns new access token, refresh token, and user information.
    """
    payload = verify_token(request.refresh_token, db)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token(data={"sub": str(user.id), "email": user.email})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's information.
    
    Requires valid access token in Authorization header.
    """
    return current_user


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout endpoint - blacklists the current access token.
    
    Adds the current token to blacklist so it cannot be used again.
    Client should also discard both access and refresh tokens.
    """
    from app.security import blacklist_token, verify_token
    from datetime import datetime
    
    token = credentials.credentials
    
    # Decode token to get expiration
    payload = verify_token(token, db)
    if payload:
        expires_at = datetime.fromtimestamp(payload.get("exp"))
        blacklist_token(token, str(current_user.id), expires_at, db)
    
    return {"message": "Logged out successfully. Token has been invalidated."}
