from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Attendance(SQLModel, table=True):
    __tablename__ = "attendance"
    __table_args__ = (
        UniqueConstraint("student_id", "date", "period", name="uq_student_date_period"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    section_id: int = Field(foreign_key="sections.id")
    date: date
    period: int
    status: str
    marked_by_user_id: int = Field(foreign_key="users.id")


class Mark(SQLModel, table=True):
    __tablename__ = "marks"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    subject_id: int = Field(foreign_key="subjects.id")
    exam_type: str
    max_marks: float
    marks_obtained: float
    entered_by_user_id: int = Field(foreign_key="users.id")


class Exam(SQLModel, table=True):
    __tablename__ = "exams"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    department_id: int = Field(foreign_key="departments.id")
    year: int
    semester: int
    start_date: date
    end_date: date
    is_published: bool = Field(default=False)


class ExamSchedule(SQLModel, table=True):
    __tablename__ = "exam_schedules"

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id")
    subject_id: int = Field(foreign_key="subjects.id")
    exam_date: date
    session: str
    room: str


class HallTicket(SQLModel, table=True):
    __tablename__ = "hall_tickets"

    id: Optional[int] = Field(default=None, primary_key=True)
    exam_id: int = Field(foreign_key="exams.id")
    student_id: int = Field(foreign_key="students.id")
    ticket_no: str = Field(unique=True, index=True)
    is_eligible: bool = Field(default=True)
    reason: Optional[str] = Field(default=None)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LeaveRequest(SQLModel, table=True):
    __tablename__ = "leave_requests"

    id: Optional[int] = Field(default=None, primary_key=True)
    student_id: int = Field(foreign_key="students.id")
    from_date: date
    to_date: date
    reason: str
    status: str = Field(default="pending")
    decided_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")


class Notice(SQLModel, table=True):
    __tablename__ = "notices"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: str
    audience: str
    department_id: Optional[int] = Field(default=None, foreign_key="departments.id")
    section_id: Optional[int] = Field(default=None, foreign_key="sections.id")
    role: Optional[str] = Field(default=None)
    created_by_user_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))