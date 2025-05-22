from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.schemas.user import User
from app.database import get_db

router = APIRouter()

@router.get("/random", response_model=User)
async def random_user(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_random_user()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return user

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
