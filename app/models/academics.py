from datetime import date, datetime, timezone
from typing import Optional
from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from app.models.users import User


class Department(SQLModel, table=True):
    __tablename__ = "departments"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    name: str
    intake: int = Field(default=120)
    hod_user_id: Optional[int] = Field(default=None, foreign_key="users.id")


class Batch(SQLModel, table=True):
    __tablename__ = "batches"

    id: Optional[int] = Field(default=None, primary_key=True)
    department_id: int = Field(foreign_key="departments.id")
    start_year: int
    end_year: int


class Section(SQLModel, table=True):
    __tablename__ = "sections"

    id: Optional[int] = Field(default=None, primary_key=True)
    batch_id: int = Field(foreign_key="batches.id")
    name: str
    current_year: int = Field(default=1)
    current_semester: int = Field(default=1)
    capacity: int = Field(default=60)


class MentorGroup(SQLModel, table=True):
    __tablename__ = "mentor_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    section_id: int = Field(foreign_key="sections.id")
    name: str
    mentor_user_id: int = Field(foreign_key="users.id")
    capacity: int = Field(default=30)


class Student(SQLModel, table=True):
    __tablename__ = "students"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(unique=True, foreign_key="users.id")
    roll_number: str = Field(unique=True, index=True)
    full_name: str
    dob: date
    gender: str
    phone: str
    email: str
    parent_name: str
    department_id: int = Field(foreign_key="departments.id")
    batch_id: int = Field(foreign_key="batches.id")
    section_id: int = Field(foreign_key="sections.id")
    mentor_group_id: Optional[int] = Field(default=None, foreign_key="mentor_groups.id")
    quota: str
    admission_year: int
    status: str = Field(default="active")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional[User] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Student.user_id]"}
    )
    department: Optional[Department] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Student.department_id]"}
    )
    section: Optional[Section] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Student.section_id]"}
    )
    mentor_group: Optional[MentorGroup] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Student.mentor_group_id]"}
    )


class Subject(SQLModel, table=True):
    __tablename__ = "subjects"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    name: str
    department_id: int = Field(foreign_key="departments.id")
    year: int
    semester: int
    credits: int


class TeachingAssignment(SQLModel, table=True):
    __tablename__ = "teaching_assignments"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_id: int = Field(foreign_key="subjects.id")
    section_id: int = Field(foreign_key="sections.id")
    teacher_user_id: int = Field(foreign_key="users.id")


class RollCounter(SQLModel, table=True):
    __tablename__ = "roll_counters"
    __table_args__ = (
        UniqueConstraint("department_id", "admission_year", name="uq_dept_admission_year"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    department_id: int = Field(foreign_key="departments.id")
    admission_year: int
    last_serial: int = Field(default=0)