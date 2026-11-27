from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel


class Role(str, Enum):
    management = "management"
    hod = "hod"
    mentor = "mentor"
    trainer = "trainer"
    student = "student"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    full_name: str
    email: Optional[str] = Field(default=None, index=True)
    password_hash: str
    role: Role
    department_id: Optional[int] = Field(default=None, foreign_key="departments.id")
    is_active: bool = Field(default=True)
    must_change_password: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))