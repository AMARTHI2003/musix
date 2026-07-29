from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from auth import get_current_user
from models import User
from schemas import User as UserSchema

router = APIRouter(prefix="/auth", tags=["Authentication"])

from pydantic import BaseModel
import uuid
from auth import create_access_token

class LoginRequest(BaseModel):
    name: str
    email: str

@router.post("/custom_login")
async def custom_login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Simple one-time login that generates a JWT."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Create user with a generated ID
        new_id = str(uuid.uuid4())
        user = User(id=new_id, email=data.email, username=data.name)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
    token = create_access_token({"sub": user.email, "is_admin": True}) # Assign admin loosely for now based on request
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserSchema)
async def get_me(user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return user

@router.put("/me")
async def update_profile(
    username: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's username."""
    user.username = username
    await db.commit()
    await db.refresh(user)
    return {"message": "Profile updated", "username": user.username}

@router.get("/health")
async def health_check():
    """Public health check endpoint."""
    return {"status": "ok", "service": "Harmony Music API"}
