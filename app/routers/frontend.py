from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_repository import UserRepository
from app.services.random_user_service import RandomUserService
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, page: int = 1, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    per_page = 20
    total_users = await repo.count_users()
    users = await repo.get_users(skip=(page - 1) * per_page, limit=per_page)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "users": users,
        "page": page,
        "total_pages": (total_users + per_page - 1) // per_page
    })


@router.post("/load-users")
async def load_users(
        request: Request,
        count: int = Form(...),
        db: AsyncSession = Depends(get_db)
):
    if count < 1 or count > 5000:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Count must be between 1 and 5000"},
            status_code=400
        )

    try:
        repo = UserRepository(db)
        service = RandomUserService(repo)
        await service.load_users(count)
        return RedirectResponse(url="/", status_code=303)
    except Exception as e:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(e)},
            status_code=400
        )


@router.get("/user/{user_id}", response_class=HTMLResponse)
async def read_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse("user_detail.html", {"request": request, "user": user})


@router.get("/random", response_class=HTMLResponse)
async def random_user(request: Request, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_random_user()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return templates.TemplateResponse("user_detail.html", {"request": request, "user": user})