from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, text
from app.models.user import User
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

    return templates.TemplateResponse(request, "index.html", {
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
    repo = UserRepository(db)
    
    users = await repo.get_users()
    per_page = 10
    current_page = 1
    total_pages = max(1, (len(users) + per_page - 1) // per_page)
    
    if count < 1 or count > 5000:
        return templates.TemplateResponse(request, "index.html",
            {
                "error": "Count must be between 1 and 5000",
                "users": users[:per_page],
                "page": current_page,
                "total_pages": total_pages
            },
            status_code=400
        )

    try:
        service = RandomUserService(repo)
        await service.load_users(count)
        return RedirectResponse(url="/", status_code=303)
    
    except Exception as e:
        return templates.TemplateResponse(request, "index.html",
            {
                "error": str(e),
                "users": users[:per_page],
                "page": current_page,
                "total_pages": total_pages
            },
            status_code=400
        )



@router.get("/random", response_class=HTMLResponse)
async def random_user(request: Request, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_random_user()
    if not user:
        raise HTTPException(status_code=404, detail="No users found")
    return templates.TemplateResponse(request, "user_detail.html", {"user": user})


@router.get("/admin/clear")
async def clear_users_table(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("TRUNCATE TABLE users RESTART IDENTITY CASCADE"))
        await db.commit()
        
        return RedirectResponse(
            url="/?message=Clear_DB",
            status_code=303
        )
    except Exception as e:
        await db.rollback()
        return RedirectResponse(
            url=f"/?error=Clear+failed:{str(e).replace(' ', '+')}",
            status_code=303
        )

@router.get("/{user_id}", response_class=HTMLResponse)
async def read_user(user_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return templates.TemplateResponse(request, "user_detail.html", {"user": user})


