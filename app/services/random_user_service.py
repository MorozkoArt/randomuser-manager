import httpx
from typing import List, Dict, Any
from app.config import settings
from app.repositories.user_repository import UserRepository

class RandomUserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def fetch_users(self, count: int) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                str(settings.RANDOM_USER_API),
                params={"results": count}
            )
            response.raise_for_status()
            data = response.json()
            return data["results"]

    async def load_users(self, count: int) -> None:
        if count <= 0:
            raise ValueError("Count must be positive")
            
        users_data = await self.fetch_users(count)
        for user_data in users_data:
            try:
                user_dict = {
                    "gender": user_data["gender"],
                    "first_name": user_data["name"]["first"],
                    "last_name": user_data["name"]["last"],
                    "email": user_data["email"],
                    "phone": user_data["phone"],
                    "location": str(user_data["location"]),
                    "picture_url": user_data["picture"]["thumbnail"]
                }
                await self.repository.create_user(user_dict)
            except Exception as e:
                continue