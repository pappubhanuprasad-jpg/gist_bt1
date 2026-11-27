from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.admin import setup_admin
from app.config import settings
from app.database import create_db_and_tables
from app.deps import NotAuthenticatedException
from app.routers import auth, hod, management, mentor, register, student, trainer

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.exception_handler(NotAuthenticatedException)
async def not_authenticated_handler(request: Request, exc: NotAuthenticatedException):
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        request=request,
        name="403.html",
        context={"page_title": "Access Denied"},
        status_code=status.HTTP_403_FORBIDDEN,
    )


app.include_router(auth.router)
app.include_router(register.router)
app.include_router(hod.router)
app.include_router(management.router)
app.include_router(mentor.router)
app.include_router(trainer.router)
app.include_router(student.router)

setup_admin(app)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)