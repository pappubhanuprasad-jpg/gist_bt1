from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.deps import require_role
from app.models.academics import Batch, Department, MentorGroup, Section, Student
from app.models.users import Role, User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(prefix="/mentor", tags=["Mentor"])


def _build_mentor_menu(active_url: str) -> list[dict]:
    return [
        {"label": "Dashboard", "url": "/mentor", "active": active_url == "/mentor"},
        {"label": "Mark Attendance", "url": "#", "disabled": True, "tag": "Day 2"},
        {"label": "Leave Approvals", "url": "#", "disabled": True, "tag": "Day 2"},
    ]


@router.get("", response_class=HTMLResponse)
def mentor_dashboard(
    request: Request,
    current_user: User = Depends(require_role(Role.mentor)),
    session: Session = Depends(get_session),
):
    group = session.exec(
        select(MentorGroup).where(MentorGroup.mentor_user_id == current_user.id)
    ).first()

    section = session.get(Section, group.section_id) if group else None
    batch = session.get(Batch, section.batch_id) if section else None
    dept = session.get(Department, batch.department_id) if batch else None

    students = []
    if group:
        students = session.exec(
            select(Student)
            .where(Student.mentor_group_id == group.id)
            .order_by(Student.roll_number)
        ).all()

    return templates.TemplateResponse(
        request=request,
        name="mentor/dashboard.html",
        context={
            "page_title": "Mentor Dashboard",
            "current_user": current_user,
            "menu_items": _build_mentor_menu("/mentor"),
            "group": group,
            "section": section,
            "batch": batch,
            "department": dept,
            "students": students,
        },
    )