from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.deps import get_current_user
from app.models.users import Role, User
from app.security import create_access_token, hash_password, verify_password

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(tags=["Authentication"])

ROLE_DASHBOARD_MAP: dict[str, str] = {
    Role.management.value: "/management",
    Role.hod.value: "/hod",
    Role.mentor.value: "/mentor",
    Role.trainer.value: "/trainer",
    Role.student.value: "/student",
}


def _dashboard_url_for_role(role: Role | str) -> str:
    role_str = role.value if isinstance(role, Role) else str(role)
    return ROLE_DASHBOARD_MAP.get(role_str, "/login")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"page_title": "Sign In", "error": None, "username": ""},
    )


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    cleaned_username = username.strip()
    user = session.exec(select(User).where(User.username == cleaned_username)).first()

    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "page_title": "Sign In",
                "error": "Wrong username or password",
                "username": cleaned_username,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token = create_access_token(user_id=user.id, role=user.role.value)
    target_url = "/change-password" if user.must_change_password else _dashboard_url_for_role(user.role)

    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
    )
    return response


@router.get("/change-password", response_class=HTMLResponse)
def change_password_page(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        request=request,
        name="change_password.html",
        context={
            "page_title": "Change Password",
            "current_user": current_user,
            "error": None,
        },
    )


@router.post("/change-password", response_class=HTMLResponse)
def change_password_submit(
    request: Request,
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if len(new_password) < 8:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "page_title": "Change Password",
                "current_user": current_user,
                "error": "New password must be at least 8 characters long.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if new_password != confirm_password:
        return templates.TemplateResponse(
            request=request,
            name="change_password.html",
            context={
                "page_title": "Change Password",
                "current_user": current_user,
                "error": "Passwords do not match. Please try again.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    current_user.password_hash = hash_password(new_password)
    current_user.must_change_password = False
    session.add(current_user)
    session.commit()

    target_url = _dashboard_url_for_role(current_user.role)
    return RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response