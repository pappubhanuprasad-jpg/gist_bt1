from datetime import date, datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class RegistrationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    correction = "correction"


class Registration(SQLModel, table=True):
    __tablename__ = "registrations"

    id: Optional[int] = Field(default=None, primary_key=True)
    reference_no: str = Field(unique=True, index=True)
    full_name: str
    dob: date
    gender: str
    phone: str
    email: str
    parent_name: str
    department_id: int = Field(foreign_key="departments.id")
    quota: str
    entrance_rank: Optional[int] = Field(default=None)
    tenth_percent: float
    inter_percent: float
    photo_path: Optional[str] = Field(default=None)
    marks_memo_path: Optional[str] = Field(default=None)
    id_proof_path: Optional[str] = Field(default=None)
    status: RegistrationStatus = Field(default=RegistrationStatus.pending)
    hod_remarks: Optional[str] = Field(default=None)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decided_at: Optional[datetime] = Field(default=None)
    decided_by_user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    student_id: Optional[int] = Field(default=None, foreign_key="students.id")