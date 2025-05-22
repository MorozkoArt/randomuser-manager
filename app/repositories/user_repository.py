from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user_data: dict) -> User:
        user = User(**user_data)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalars().first()

    async def get_random_user(self) -> Optional[User]:
        result = await self.session.execute(
            select(User).order_by(func.random()).limit(1)
        )
        return result.scalars().first()

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self.session.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar()