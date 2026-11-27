from fastapi import FastAPI, Request
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlmodel import Session, select

from app.config import settings
from app.database import engine
from app.models.academics import (
    Batch,
    Department,
    MentorGroup,
    Section,
    Student,
    Subject,
    TeachingAssignment,
)
from app.models.later import (
    Attendance,
    Exam,
    ExamSchedule,
    HallTicket,
    LeaveRequest,
    Mark,
    Notice,
)
from app.models.registration import Registration
from app.models.users import Role, User
from app.security import verify_password


class ManagementAdminAuth(AuthenticationBackend):
    """
    SQLAdmin authentication backend:
    - Verifies credentials against the User table.
    - Allows ONLY active users with Role.management.
    - Session cookie is signed with settings.SECRET_KEY.
    """

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", "")).strip()
        password = str(form.get("password", ""))

        if not username or not password:
            return False

        with Session(engine) as session:
            user = session.exec(select(User).where(User.username == username)).first()
            if (
                not user
                or not user.is_active
                or user.role != Role.management
                or not verify_password(password, user.password_hash)
            ):
                return False

            request.session.update({"admin_user_id": user.id})
            return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_user_id = request.session.get("admin_user_id")
        if not admin_user_id:
            return False

        with Session(engine) as session:
            user = session.get(User, int(admin_user_id))
            if not user or not user.is_active or user.role != Role.management:
                request.session.clear()
                return False
            return True


# ---------------------------------------------------------------------------
# Category 1: People
# ---------------------------------------------------------------------------
class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    category = "People"
    icon = "fa-solid fa-user-shield"

    column_list = [
        User.id,
        User.username,
        User.full_name,
        User.email,
        User.role,
        User.department_id,
        User.is_active,
        User.must_change_password,
    ]
    # AD-05: Never expose or allow editing password_hash in list, detail, or form views
    column_details_exclude_list = [User.password_hash]
    form_excluded_columns = [User.password_hash, User.created_at]
    column_searchable_list = [User.username, User.role]
    column_sortable_list = [User.id, User.username, User.role, User.is_active]


class StudentAdmin(ModelView, model=Student):
    name = "Student"
    name_plural = "Students"
    category = "People"
    icon = "fa-solid fa-user-graduate"

    column_list = [
        Student.id,
        Student.roll_number,
        Student.full_name,
        Student.department,
        Student.section,
        Student.quota,
        Student.status,
    ]
    column_searchable_list = [Student.roll_number, Student.full_name]
    column_sortable_list = [Student.id, Student.roll_number, Student.full_name, Student.status]


# ---------------------------------------------------------------------------
# Category 2: Academics
# ---------------------------------------------------------------------------
class DepartmentAdmin(ModelView, model=Department):
    name = "Department"
    name_plural = "Departments"
    category = "Academics"
    icon = "fa-solid fa-building-columns"

    column_list = [Department.id, Department.code, Department.name, Department.intake, Department.hod_user_id]
    column_searchable_list = [Department.code, Department.name]


class BatchAdmin(ModelView, model=Batch):
    name = "Batch"
    name_plural = "Batches"
    category = "Academics"
    icon = "fa-solid fa-calendar-days"

    column_list = [Batch.id, Batch.department_id, Batch.start_year, Batch.end_year]


class SectionAdmin(ModelView, model=Section):
    name = "Section"
    name_plural = "Sections"
    category = "Academics"
    icon = "fa-solid fa-layer-group"

    column_list = [
        Section.id,
        Section.batch_id,
        Section.name,
        Section.current_year,
        Section.current_semester,
        Section.capacity,
    ]


class MentorGroupAdmin(ModelView, model=MentorGroup):
    name = "Mentor group"
    name_plural = "Mentor groups"
    category = "Academics"
    icon = "fa-solid fa-users-rectangle"

    column_list = [
        MentorGroup.id,
        MentorGroup.name,
        MentorGroup.section_id,
        MentorGroup.mentor_user_id,
        MentorGroup.capacity,
    ]
    column_searchable_list = [MentorGroup.name]


class SubjectAdmin(ModelView, model=Subject):
    name = "Subject"
    name_plural = "Subjects"
    category = "Academics"
    icon = "fa-solid fa-book"

    column_list = [
        Subject.id,
        Subject.code,
        Subject.name,
        Subject.department_id,
        Subject.year,
        Subject.semester,
        Subject.credits,
    ]
    column_searchable_list = [Subject.code, Subject.name]


class TeachingAssignmentAdmin(ModelView, model=TeachingAssignment):
    name = "Teaching assignment"
    name_plural = "Teaching assignments"
    category = "Academics"
    icon = "fa-solid fa-chalkboard-user"

    column_list = [
        TeachingAssignment.id,
        TeachingAssignment.subject_id,
        TeachingAssignment.section_id,
        TeachingAssignment.teacher_user_id,
    ]


# ---------------------------------------------------------------------------
# Category 3: Admissions
# ---------------------------------------------------------------------------
class RegistrationAdmin(ModelView, model=Registration):
    name = "Registration"
    name_plural = "Registrations"
    category = "Admissions"
    icon = "fa-solid fa-file-signature"

    column_list = [
        Registration.id,
        Registration.reference_no,
        Registration.full_name,
        Registration.department_id,
        Registration.quota,
        Registration.inter_percent,
        Registration.status,
        Registration.student_id,
    ]
    column_searchable_list = [Registration.reference_no, Registration.status]
    column_sortable_list = [Registration.id, Registration.reference_no, Registration.status]


# ---------------------------------------------------------------------------
# Category 4: Exams and attendance
# ---------------------------------------------------------------------------
class AttendanceAdmin(ModelView, model=Attendance):
    name = "Attendance"
    name_plural = "Attendance"
    category = "Exams and attendance"
    icon = "fa-solid fa-clipboard-check"

    column_list = [
        Attendance.id,
        Attendance.student_id,
        Attendance.section_id,
        Attendance.date,
        Attendance.period,
        Attendance.status,
        Attendance.marked_by_user_id,
    ]


class MarkAdmin(ModelView, model=Mark):
    name = "Mark"
    name_plural = "Marks"
    category = "Exams and attendance"
    icon = "fa-solid fa-pen-to-square"

    column_list = [
        Mark.id,
        Mark.student_id,
        Mark.subject_id,
        Mark.exam_type,
        Mark.marks_obtained,
        Mark.max_marks,
        Mark.entered_by_user_id,
    ]


class ExamAdmin(ModelView, model=Exam):
    name = "Exam"
    name_plural = "Exams"
    category = "Exams and attendance"
    icon = "fa-solid fa-file-pen"

    column_list = [
        Exam.id,
        Exam.name,
        Exam.department_id,
        Exam.year,
        Exam.semester,
        Exam.start_date,
        Exam.end_date,
        Exam.is_published,
    ]


class ExamScheduleAdmin(ModelView, model=ExamSchedule):
    name = "Exam schedule"
    name_plural = "Exam schedules"
    category = "Exams and attendance"
    icon = "fa-solid fa-clock"

    column_list = [
        ExamSchedule.id,
        ExamSchedule.exam_id,
        ExamSchedule.subject_id,
        ExamSchedule.exam_date,
        ExamSchedule.session,
        ExamSchedule.room,
    ]


class HallTicketAdmin(ModelView, model=HallTicket):
    name = "Hall ticket"
    name_plural = "Hall tickets"
    category = "Exams and attendance"
    icon = "fa-solid fa-id-card"

    column_list = [
        HallTicket.id,
        HallTicket.ticket_no,
        HallTicket.exam_id,
        HallTicket.student_id,
        HallTicket.is_eligible,
        HallTicket.generated_at,
    ]
    column_searchable_list = [HallTicket.ticket_no]


class LeaveRequestAdmin(ModelView, model=LeaveRequest):
    name = "Leave request"
    name_plural = "Leave requests"
    category = "Exams and attendance"
    icon = "fa-solid fa-envelope-open-text"

    column_list = [
        LeaveRequest.id,
        LeaveRequest.student_id,
        LeaveRequest.from_date,
        LeaveRequest.to_date,
        LeaveRequest.status,
        LeaveRequest.decided_by_user_id,
    ]


class NoticeAdmin(ModelView, model=Notice):
    name = "Notice"
    name_plural = "Notices"
    category = "Exams and attendance"
    icon = "fa-solid fa-bullhorn"

    column_list = [
        Notice.id,
        Notice.title,
        Notice.audience,
        Notice.department_id,
        Notice.section_id,
        Notice.role,
        Notice.created_at,
    ]


def setup_admin(app: FastAPI) -> Admin:
    """Attach SQLAdmin at /admin with Management-only session authentication."""
    auth_backend = ManagementAdminAuth(secret_key=settings.SECRET_KEY)
    admin = Admin(
        app=app,
        engine=engine,
        title="B.Tech SMS Admin",
        base_url="/admin",
        templates_dir="app/templates",
        authentication_backend=auth_backend,
    )

    # People
    admin.add_view(UserAdmin)
    admin.add_view(StudentAdmin)

    # Academics
    admin.add_view(DepartmentAdmin)
    admin.add_view(BatchAdmin)
    admin.add_view(SectionAdmin)
    admin.add_view(MentorGroupAdmin)
    admin.add_view(SubjectAdmin)
    admin.add_view(TeachingAssignmentAdmin)

    # Admissions
    admin.add_view(RegistrationAdmin)

    # Exams and attendance
    admin.add_view(AttendanceAdmin)
    admin.add_view(MarkAdmin)
    admin.add_view(ExamAdmin)
    admin.add_view(ExamScheduleAdmin)
    admin.add_view(HallTicketAdmin)
    admin.add_view(LeaveRequestAdmin)
    admin.add_view(NoticeAdmin)

    return admin