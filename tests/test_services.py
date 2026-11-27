from datetime import date
import unittest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.models.academics import Batch, Department, MentorGroup, Section, Student
from app.models.registration import Registration, RegistrationStatus
from app.models.users import Role, User
from app.services.approval import approve_registration
from app.services.placement import pick_mentor_group
from app.services.roll_number import next_roll_number


class TestPlacementAndApprovalServices(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

        self.dept = Department(code="CSE", name="Computer Science and Engineering", intake=120)
        self.session.add(self.dept)
        self.session.commit()
        self.session.refresh(self.dept)

        self.hod = User(
            username="hod.cse@college.edu",
            full_name="Dr. Ramesh Kumar",
            email="hod.cse@college.edu",
            password_hash="hashed",
            role=Role.hod,
            department_id=self.dept.id,
        )
        self.session.add(self.hod)
        self.session.commit()
        self.session.refresh(self.hod)

    def tearDown(self) -> None:
        self.session.close()

    def test_roll_number_serials_increment_001_002_003(self) -> None:
        r1 = next_roll_number(self.session, self.dept, 2026)
        r2 = next_roll_number(self.session, self.dept, 2026)
        r3 = next_roll_number(self.session, self.dept, 2026)

        self.assertEqual(r1, "26CSE001")
        self.assertEqual(r2, "26CSE002")
        self.assertEqual(r3, "26CSE003")

    def test_full_mentor_group_of_30_is_skipped(self) -> None:
        batch = Batch(department_id=self.dept.id, start_year=2026, end_year=2030)
        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)

        section = Section(batch_id=batch.id, name="A", current_year=1, current_semester=1, capacity=60)
        self.session.add(section)
        self.session.commit()
        self.session.refresh(section)

        mentor1 = User(
            username="mentor1@college.edu",
            full_name="Mentor One",
            email="mentor1@college.edu",
            password_hash="hashed",
            role=Role.mentor,
            department_id=self.dept.id,
        )
        mentor2 = User(
            username="mentor2@college.edu",
            full_name="Mentor Two",
            email="mentor2@college.edu",
            password_hash="hashed",
            role=Role.mentor,
            department_id=self.dept.id,
        )
        self.session.add_all([mentor1, mentor2])
        self.session.commit()
        self.session.refresh(mentor1)
        self.session.refresh(mentor2)

        group_full = MentorGroup(section_id=section.id, name="CSE-A Group 1", mentor_user_id=mentor1.id, capacity=30)
        group_open = MentorGroup(section_id=section.id, name="CSE-A Group 2", mentor_user_id=mentor2.id, capacity=30)
        self.session.add_all([group_full, group_open])
        self.session.commit()
        self.session.refresh(group_full)
        self.session.refresh(group_open)

        # Fill group_full with 30 students
        for i in range(1, 31):
            u = User(
                username=f"26CSE{i:03d}",
                full_name=f"Student {i}",
                email=f"s{i}@college.edu",
                password_hash="hashed",
                role=Role.student,
                department_id=self.dept.id,
            )
            self.session.add(u)
            self.session.flush()
            self.session.add(
                Student(
                    user_id=u.id,
                    roll_number=f"26CSE{i:03d}",
                    full_name=f"Student {i}",
                    dob=date(2008, 1, 1),
                    gender="Male",
                    phone="9876543210",
                    email=f"s{i}@college.edu",
                    parent_name="Parent",
                    department_id=self.dept.id,
                    batch_id=batch.id,
                    section_id=section.id,
                    mentor_group_id=group_full.id,
                    quota="convener",
                    admission_year=2026,
                )
            )
        self.session.commit()

        picked = pick_mentor_group(self.session, section)
        self.assertIsNotNone(picked)
        self.assertEqual(picked.id, group_open.id)

    def test_second_approve_call_fails(self) -> None:
        reg = Registration(
            reference_no="REG-2026-00001",
            full_name="Aarav Sharma",
            dob=date(2008, 5, 10),
            gender="Male",
            phone="9876543210",
            email="aarav@example.com",
            parent_name="Rajesh Sharma",
            department_id=self.dept.id,
            quota="convener",
            tenth_percent=92.0,
            inter_percent=90.5,
            photo_path="/static/photo.jpg",
            marks_memo_path="/static/memo.pdf",
            id_proof_path="/static/id.pdf",
            status=RegistrationStatus.pending,
        )
        self.session.add(reg)
        self.session.commit()
        self.session.refresh(reg)

        result = approve_registration(self.session, reg, self.hod)
        self.assertEqual(result["roll_number"], "26CSE001")
        self.assertEqual(len(result["temp_password"]), 8)

        with self.assertRaises(ValueError):
            approve_registration(self.session, reg, self.hod)


if __name__ == "__main__":
    unittest.main()