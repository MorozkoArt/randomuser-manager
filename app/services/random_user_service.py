import httpx
from app.config import settings
from app.repositories.user_repository import UserRepository

class RandomUserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def fetch_users(self, count: int):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                settings.RANDOM_USER_API,
                params={"results": count}
            )
            response.raise_for_status()
            data = response.json()
            return data["results"]

    async def load_users(self, count: int):
        users_data = await self.fetch_users(count)
        for user_data in users_data:
            try:
                await self.repository.create_user({
                    "gender": user_data["gender"],
                    "first_name": user_data["name"]["first"],
                    "last_name": user_data["name"]["last"],
                    "email": user_data["email"],
                    "phone": user_data["phone"],
                    "location": str(user_data["location"]),
                    "picture_url": user_data["picture"]["thumbnail"]
                })
            except Exception:
                continue