from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, Base
from app.routers import api, frontend

from app.database import get_db
import os

app = FastAPI()

app.include_router(api.router, prefix="/api/v1")
app.include_router(frontend.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await init_db_data()


async def init_db_data():
    from app.repositories.user_repository import UserRepository
    from app.services.random_user_service import RandomUserService
    from app.database import async_session

    async with async_session() as session:
        repo = UserRepository(session)
        if await repo.count_users() == 0:
            service = RandomUserService(repo)
            await service.load_users(1000)

# Для тестов
async def override_get_db():
    from app.database import async_session
    async with async_session() as session:
        yield session

if os.getenv("TESTING"):
    app.dependency_overrides[get_db] = override_get_db

