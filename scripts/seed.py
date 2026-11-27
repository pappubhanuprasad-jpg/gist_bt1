from datetime import date, datetime, timedelta, timezone
import random
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from faker import Faker
from sqlmodel import Session, SQLModel, func, select

import app.models  # noqa: F401
from app.database import engine
from app.models.academics import (
    Batch,
    Department,
    MentorGroup,
    RollCounter,
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
from app.models.registration import Registration, RegistrationStatus
from app.models.users import Role, User
from app.security import hash_password
from app.services.roll_number import next_roll_number

DEPARTMENTS_DATA = [
    ("CSE", "Computer Science and Engineering", 120),
    ("ECE", "Electronics and Communication Engineering", 120),
    ("EEE", "Electrical and Electronics Engineering", 120),
    ("MECH", "Mechanical Engineering", 120),
    ("CIVIL", "Civil Engineering", 120),
]

BATCH_YEAR_CONFIG = [
    (2026, 1, 1),  # 1st Year, Sem 1
    (2025, 2, 3),  # 2nd Year, Sem 3
    (2024, 3, 5),  # 3rd Year, Sem 5
    (2023, 4, 7),  # 4th Year, Sem 7
]

SUBJECT_TEMPLATES = {
    1: [
        ("101", "Engineering Mathematics - I", 4),
        ("102", "Engineering Physics", 4),
        ("103", "Programming for Problem Solving", 4),
        ("104", "Basic Electrical Engineering", 3),
        ("105", "Engineering Graphics & Design", 3),
        ("106", "Communicative English", 2),
    ],
    2: [
        ("201", "Probability & Statistics", 4),
        ("202", "Core Circuit & Logic Systems", 4),
        ("203", "Data Structures & Algorithms", 4),
        ("204", "Object Oriented Programming", 3),
        ("205", "Discrete Mathematics", 3),
        ("206", "Environmental Science", 2),
    ],
    3: [
        ("301", "Design & Analysis of Algorithms", 4),
        ("302", "Database Management Systems", 4),
        ("303", "Operating Systems", 4),
        ("304", "Computer Networks", 3),
        ("305", "Software Engineering", 3),
        ("306", "Professional Ethics & Values", 2),
    ],
    4: [
        ("401", "Machine Learning & AI", 4),
        ("402", "Cloud & Distributed Systems", 4),
        ("403", "Information Security", 3),
        ("404", "Industrial Management", 3),
        ("405", "Open Elective - I", 3),
        ("406", "Major Project Phase - I", 3),
    ],
}

INDIAN_FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Krishna",
    "Ishaan", "Shaurya", "Rohan", "Karthik", "Pranav", "Nikhil", "Varun", "Harsha",
    "Ravi", "Suresh", "Mahesh", "Charan", "Teja", "Bhanu", "Tarun", "Kiran",
    "Manoj", "Deepak", "Siddharth", "Abhinav", "Gautam", "Vikram",
]

INDIAN_FIRST_NAMES_FEMALE = [
    "Ananya", "Diya", "Saanvi", "Aadhya", "Pari", "Kavya", "Divya", "Pooja",
    "Sneha", "Swathi", "Keerthi", "Harini", "Lakshmi", "Meghana", "Nandini", "Priya",
    "Shravya", "Bhavana", "Sindhu", "Aishwarya", "Roshni", "Tanvi", "Neha", "Pallavi",
    "Sowmya", "Chandana", "Mounika", "Spandana", "Gayathri", "Vaishnavi",
]

INDIAN_LAST_NAMES = [
    "Sharma", "Reddy", "Rao", "Nair", "Patel", "Kumar", "Varma", "Naidu",
    "Iyer", "Menon", "Gupta", "Verma", "Singh", "Kulkarni", "Joshi", "Deshmukh",
    "Choudhary", "Prasad", "Murthy", "Bhat", "Shetty", "Das", "Chatterjee", "Pillai",
]

INDIAN_CITIES = [
    "Hyderabad", "Nellore", "Vijayawada", "Visakhapatnam", "Tirupati",
    "Bengaluru", "Chennai", "Pune", "Warangal", "Guntur",
]


def _make_indian_person(rng: random.Random) -> tuple[str, str, str]:
    gender = rng.choice(["Male", "Female"])
    first = rng.choice(
        INDIAN_FIRST_NAMES_MALE if gender == "Male" else INDIAN_FIRST_NAMES_FEMALE
    ).capitalize()
    last = rng.choice(INDIAN_LAST_NAMES)
    return f"{first} {last}", gender, last


def _make_indian_phone(rng: random.Random) -> str:
    first_digit = rng.choice(["9", "8", "7", "6"])
    rest = "".join(str(rng.randint(0, 9)) for _ in range(9))
    return first_digit + rest


def _get_last_six_working_days(today: date) -> list[date]:
    """Return the 6 most recent Monday–Saturday dates strictly before `today`."""
    days: list[date] = []
    cursor = today - timedelta(days=1)
    while len(days) < 6:
        if cursor.weekday() != 6:  # 6 == Sunday
            days.append(cursor)
        cursor -= timedelta(days=1)
    days.reverse()
    return days


def seed_database() -> None:
    rng = random.Random(42)
    fake = Faker("en_IN")
    fake.seed_instance(42)

    # Always start from a fresh, empty database
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    mgmt_hash = hash_password("Admin@123")
    hod_hash = hash_password("Hod@123")
    mentor_hash = hash_password("Mentor@123")
    trainer_hash = hash_password("Trainer@123")
    student_hash = hash_password("Student@123")

    with Session(engine) as session:
        # 1. Management User
        mgmt_user = User(
            username="management@college.edu",
            full_name="Dr. Venkateswara Rao (Principal)",
            email="management@college.edu",
            password_hash=mgmt_hash,
            role=Role.management,
            is_active=True,
            must_change_password=False,
        )
        session.add(mgmt_user)
        session.flush()

        # 2. 5 Departments + 5 HODs
        departments: list[Department] = []
        hod_users: dict[str, User] = {}
        for code, name, intake in DEPARTMENTS_DATA:
            dept = Department(code=code, name=name, intake=intake)
            session.add(dept)
            session.flush()

            hod_full_name, _, _ = _make_indian_person(rng)
            hod_email = f"hod.{code.lower()}@college.edu"
            hod_user = User(
                username=hod_email,
                full_name=f"Dr. {hod_full_name}",
                email=hod_email,
                password_hash=hod_hash,
                role=Role.hod,
                department_id=dept.id,
                is_active=True,
                must_change_password=False,
            )
            session.add(hod_user)
            session.flush()

            dept.hod_user_id = hod_user.id
            session.add(dept)
            departments.append(dept)
            hod_users[code] = hod_user

        # 3. 3 External Trainers
        trainers: list[User] = []
        for idx in range(1, 4):
            t_name, _, _ = _make_indian_person(rng)
            t_email = f"trainer{idx}@college.edu"
            trainer = User(
                username=t_email,
                full_name=f"Prof. {t_name}",
                email=t_email,
                password_hash=trainer_hash,
                role=Role.trainer,
                is_active=True,
                must_change_password=False,
            )
            session.add(trainer)
            session.flush()
            trainers.append(trainer)

        # 4. Batches, Sections, Mentor Groups & 500 Students
        section_counter = 0
        sample_mentor_username = ""
        sample_student_username = ""
        all_sections_by_dept_year: dict[tuple[int, int], list[Section]] = {}
        mentors_by_dept: dict[int, list[User]] = {d.id: [] for d in departments}
        section_mentor_map: dict[int, int] = {}
        all_students: list[Student] = []

        for dept in departments:
            for start_year, current_year, current_sem in BATCH_YEAR_CONFIG:
                batch = Batch(
                    department_id=dept.id,
                    start_year=start_year,
                    end_year=start_year + 4,
                )
                session.add(batch)
                session.flush()

                all_sections_by_dept_year[(dept.id, current_year)] = []

                for sec_name in ("A", "B"):
                    section = Section(
                        batch_id=batch.id,
                        name=sec_name,
                        current_year=current_year,
                        current_semester=current_sem,
                        capacity=60,
                    )
                    session.add(section)
                    session.flush()
                    all_sections_by_dept_year[(dept.id, current_year)].append(section)

                    mentor_name, _, _ = _make_indian_person(rng)
                    mentor_email = f"mentor.{dept.code.lower()}.{start_year}{sec_name.lower()}@college.edu"
                    if not sample_mentor_username:
                        sample_mentor_username = mentor_email

                    mentor_user = User(
                        username=mentor_email,
                        full_name=f"Prof. {mentor_name}",
                        email=mentor_email,
                        password_hash=mentor_hash,
                        role=Role.mentor,
                        department_id=dept.id,
                        is_active=True,
                        must_change_password=False,
                    )
                    session.add(mentor_user)
                    session.flush()
                    mentors_by_dept[dept.id].append(mentor_user)
                    section_mentor_map[section.id] = mentor_user.id

                    mentor_group = MentorGroup(
                        section_id=section.id,
                        name=f"{dept.code}-{start_year}{sec_name} Group 1",
                        mentor_user_id=mentor_user.id,
                        capacity=30,
                    )
                    session.add(mentor_group)
                    session.flush()

                    num_students = 13 if (section_counter % 2 == 0) else 12
                    section_counter += 1

                    for _ in range(num_students):
                        roll_no = next_roll_number(session, dept, start_year)
                        if not sample_student_username:
                            sample_student_username = roll_no

                        s_name, gender, last_name = _make_indian_person(rng)
                        parent_first = rng.choice(INDIAN_FIRST_NAMES_MALE)
                        city = rng.choice(INDIAN_CITIES)
                        birth_year = start_year - 18
                        dob = date(birth_year, rng.randint(1, 12), rng.randint(1, 28))
                        email = f"{roll_no.lower()}@student.college.edu"

                        s_user = User(
                            username=roll_no,
                            full_name=s_name,
                            email=email,
                            password_hash=student_hash,
                            role=Role.student,
                            department_id=dept.id,
                            is_active=True,
                            must_change_password=False,
                        )
                        session.add(s_user)
                        session.flush()

                        student = Student(
                            user_id=s_user.id,
                            roll_number=roll_no,
                            full_name=f"{s_name} ({city})",
                            dob=dob,
                            gender=gender,
                            phone=_make_indian_phone(rng),
                            email=email,
                            parent_name=f"{parent_first} {last_name}",
                            department_id=dept.id,
                            batch_id=batch.id,
                            section_id=section.id,
                            mentor_group_id=mentor_group.id,
                            quota=rng.choices(["convener", "management", "spot"], weights=[70, 25, 5])[0],
                            admission_year=start_year,
                            status="active",
                        )
                        session.add(student)
                        session.flush()
                        all_students.append(student)

        # 5. Subjects (6 per dept per year) & Teaching Assignments
        for dept in departments:
            dept_mentors = mentors_by_dept[dept.id]
            for year_num in range(1, 5):
                sem_num = (year_num * 2) - 1
                sections_for_year = all_sections_by_dept_year[(dept.id, year_num)]
                for idx, (num_suffix, sub_name, credits) in enumerate(SUBJECT_TEMPLATES[year_num]):
                    subject = Subject(
                        code=f"{dept.code}{num_suffix}",
                        name=sub_name,
                        department_id=dept.id,
                        year=year_num,
                        semester=sem_num,
                        credits=credits,
                    )
                    session.add(subject)
                    session.flush()

                    for sec in sections_for_year:
                        if (idx + sec.id) % 3 == 0:
                            teacher = trainers[(idx + dept.id) % len(trainers)]
                        else:
                            teacher = dept_mentors[(idx + sec.id) % len(dept_mentors)]

                        session.add(
                            TeachingAssignment(
                                subject_id=subject.id,
                                section_id=sec.id,
                                teacher_user_id=teacher.id,
                            )
                        )

        # 6. Registrations per department: 6 pending, 1 correction, 1 rejected
        reg_serial = 1
        for dept in departments:
            status_plan = (
                [RegistrationStatus.pending] * 6
                + [RegistrationStatus.correction]
                + [RegistrationStatus.rejected]
            )
            for st in status_plan:
                applicant_name, gender, last_name = _make_indian_person(rng)
                parent_first = rng.choice(INDIAN_FIRST_NAMES_MALE)
                ref_no = f"REG-2026-{reg_serial:05d}"
                reg_serial += 1

                remarks = None
                decided_at = None
                decided_by = None
                if st == RegistrationStatus.correction:
                    remarks = "Please upload a clearer scanned copy of your Intermediate marks memo."
                    decided_at = datetime.now(timezone.utc) - timedelta(days=1)
                    decided_by = hod_users[dept.code].id
                elif st == RegistrationStatus.rejected:
                    remarks = "Minimum eligibility percentage criteria not met."
                    decided_at = datetime.now(timezone.utc) - timedelta(days=2)
                    decided_by = hod_users[dept.code].id

                session.add(
                    Registration(
                        reference_no=ref_no,
                        full_name=applicant_name,
                        dob=date(2008, rng.randint(1, 12), rng.randint(1, 28)),
                        gender=gender,
                        phone=_make_indian_phone(rng),
                        email=f"applicant{reg_serial}@example.com",
                        parent_name=f"{parent_first} {last_name}",
                        department_id=dept.id,
                        quota=rng.choice(["convener", "management", "spot"]),
                        entrance_rank=rng.randint(1200, 45000),
                        tenth_percent=round(rng.uniform(75.0, 98.5), 2),
                        inter_percent=round(rng.uniform(72.0, 97.5), 2),
                        photo_path=f"/static/uploads/registrations/{ref_no}/photo.jpg",
                        marks_memo_path=f"/static/uploads/registrations/{ref_no}/marks_memo.pdf",
                        id_proof_path=f"/static/uploads/registrations/{ref_no}/id_proof.pdf",
                        status=st,
                        hod_remarks=remarks,
                        decided_at=decided_at,
                        decided_by_user_id=decided_by,
                    )
                )

        # 7. 3 Notices
        notices_data = [
            (
                "Odd Semester Academic Calendar 2026–27",
                "Regular classwork for I, II, III, and IV B.Tech odd semesters is in progress. Minimum 75% attendance is mandatory for end-semester examinations.",
                "all",
                None,
            ),
            (
                "First-Year Orientation & Mentor Allotment",
                "All 2026 batch students must meet their assigned faculty mentors before Friday to verify their roll numbers and section details.",
                "role",
                "student",
            ),
            (
                "Faculty & Trainer Course File Submission",
                "All department mentors and external trainers are requested to finalize lesson plans and internal assessment rubrics.",
                "all",
                None,
            ),
        ]
        for title, body, audience, role_target in notices_data:
            session.add(
                Notice(
                    title=title,
                    body=body,
                    audience=audience,
                    role=role_target,
                    created_by_user_id=mgmt_user.id,
                )
            )

        # 8. Attendance History: Last 6 working days (Mon–Sat) before today, 6 periods/day (36 periods/student)
        working_days = _get_last_six_working_days(date.today())
        slots = [(d, p) for d in working_days for p in range(1, 7)]  # 36 unique (date, period) slots
        attendance_records: list[Attendance] = []
        students_below_75 = 0

        for student in all_students:
            mentor_id = section_mentor_map[student.section_id]
            tier = rng.random()
            if tier < 0.10:
                # ~10% at-risk students below 75% (absent 10 to 15 of 36 -> 58% to 72%)
                absent_count = rng.randint(10, 15)
            elif tier < 0.95:
                # ~85% normal students between 80% and 95% (absent 2 to 7 of 36 -> 80.6% to 94.4%)
                absent_count = rng.randint(2, 7)
            else:
                # ~5% high-attendance students (absent 0 or 1 of 36 -> 97.2% to 100%)
                absent_count = rng.randint(0, 1)

            if (36 - absent_count) / 36.0 < 0.75:
                students_below_75 += 1

            chosen_indices = set(rng.sample(range(36), absent_count))
            remaining_indices = [i for i in range(36) if i not in chosen_indices]
            late_count = rng.choices([0, 1, 2], weights=[70, 22, 8])[0]
            late_indices = set(rng.sample(remaining_indices, min(late_count, len(remaining_indices))))

            for idx, (att_date, period_num) in enumerate(slots):
                if idx in chosen_indices:
                    att_status = "absent"
                elif idx in late_indices:
                    att_status = "late"
                else:
                    att_status = "present"

                attendance_records.append(
                    Attendance(
                        student_id=student.id,
                        section_id=student.section_id,
                        date=att_date,
                        period=period_num,
                        status=att_status,
                        marked_by_user_id=mentor_id,
                    )
                )

        session.bulk_save_objects(attendance_records)
        session.commit()

        # Print demo credentials and table counts
        table_models = [
            ("users", User),
            ("departments", Department),
            ("batches", Batch),
            ("sections", Section),
            ("mentor_groups", MentorGroup),
            ("students", Student),
            ("subjects", Subject),
            ("teaching_assignments", TeachingAssignment),
            ("roll_counters", RollCounter),
            ("registrations", Registration),
            ("attendance", Attendance),
            ("marks", Mark),
            ("exams", Exam),
            ("exam_schedules", ExamSchedule),
            ("hall_tickets", HallTicket),
            ("leave_requests", LeaveRequest),
            ("notices", Notice),
        ]

        print("\n=== DEMO DATABASE SEEDED SUCCESSFULLY ===")
        print("\nDemo Logins (for demonstration only):")
        print("  Management : management@college.edu / Admin@123")
        print("  HOD (CSE)  : hod.cse@college.edu / Hod@123")
        print(f"  Mentor     : {sample_mentor_username} / Mentor@123")
        print("  Trainer    : trainer1@college.edu / Trainer@123")
        print(f"  Student    : {sample_student_username} / Student@123")

        print("\nTable Record Counts:")
        for table_name, model_cls in table_models:
            count = session.exec(select(func.count(model_cls.id))).one()
            print(f"  {table_name:<22}: {count}")

        print(f"\nAttendance Summary:")
        print(f"  Working dates seeded   : {working_days[0]} to {working_days[-1]} (Today skipped)")
        print(f"  Attendance records     : {len(attendance_records)}")
        print(f"  Students below 75%     : {students_below_75} / {len(all_students)}")


if __name__ == "__main__":
    seed_database()