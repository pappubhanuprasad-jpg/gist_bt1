from pathlib import Path
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, func, select

from app.database import get_session
from app.deps import require_role
from app.models.academics import (
    Batch,
    Department,
    Section,
    Student,
    Subject,
    TeachingAssignment,
)
from app.models.users import Role, User

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

router = APIRouter(prefix="/trainer", tags=["External Trainer"])


def _build_trainer_menu(active_url: str) -> list[dict]:
    return [
        {"label": "Dashboard", "url": "/trainer", "active": active_url == "/trainer"},
        {"label": "Enter Marks", "url": "#", "disabled": True, "tag": "Day 3"},
    ]


@router.get("", response_class=HTMLResponse)
def trainer_dashboard(
    request: Request,
    current_user: User = Depends(require_role(Role.trainer)),
    session: Session = Depends(get_session),
):
    assignments = session.exec(
        select(TeachingAssignment).where(
            TeachingAssignment.teacher_user_id == current_user.id
        )
    ).all()

    rows = []
    for ta in assignments:
        subject = session.get(Subject, ta.subject_id)
        section = session.get(Section, ta.section_id)
        batch = session.get(Batch, section.batch_id) if section else None
        dept = session.get(Department, batch.department_id) if batch else None
        stu_count = (
            session.exec(
                select(func.count(Student.id)).where(Student.section_id == section.id)
            ).one()
            if section
            else 0
        )
        rows.append(
            {
                "subject_code": subject.code if subject else "-",
                "subject_name": subject.name if subject else "-",
                "section_label": f"{dept.code if dept else ''}-{batch.start_year if batch else ''} Sec {section.name if section else ''}",
                "year_sem": f"Year {section.current_year} / Sem {section.current_semester}" if section else "-",
                "student_count": stu_count,
            }
        )

    return templates.TemplateResponse(
        request=request,
        name="trainer/dashboard.html",
        context={
            "page_title": "External Trainer Dashboard",
            "current_user": current_user,
            "menu_items": _build_trainer_menu("/trainer"),
            "rows": rows,
        },
    )