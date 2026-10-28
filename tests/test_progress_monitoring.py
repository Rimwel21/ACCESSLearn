import unittest
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 - register all mapped tables
from database.connection import Base
from models.HI_sections import HI_SECTIONS
from models.accounts import Accounts
from models.grade_levels import GradeLevels
from models.handsign_tutorial_practice import HandsignTutorialPractice
from models.learning_topic import LearningTopic
from models.student_profile import StudentProfile
from models.student_progress import StudentTopicProgress
from models.student_quiz_progress import StudentQuizProgress
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from services.student_module_service import (
    _complete_assessment_progress,
    _visible_topic_ids,
    update_topic_progress,
)
from services.teacher_assessment_service import _reset_progress_for_retake
from services.teacher_class_service import (
    _dashboard_progress_for_student,
    list_teacher_student_records,
)
from utils.enum import (
    AccountStatusEnum,
    RoleEnum,
    SectionStatusEnum,
    StudentType,
    VerificationStatus,
)
from utils.utc_now import utc_now


class ProgressMonitoringTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.db = self.Session()
        self._seed_classroom()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _account(self, *, username=None, email=None, role=RoleEnum.student):
        account = Accounts(
            username=username,
            email=email,
            hashed_password="test-hash",
            role=role,
            verification_status=VerificationStatus.verified,
            account_status=AccountStatusEnum.active,
        )
        self.db.add(account)
        self.db.flush()
        return account

    def _student(self, name, username, section):
        account = self._account(username=username)
        profile = StudentProfile(
            name=name,
            grade_level_id=self.grade.id,
            section_id=section.id,
            student_type=StudentType.regular,
            account_id=account.id,
        )
        self.db.add(profile)
        self.db.flush()
        return account, profile

    def _seed_classroom(self):
        self.teacher = self._account(email="science@example.com", role=RoleEnum.teacher)
        self.other_teacher = self._account(email="other@example.com", role=RoleEnum.teacher)
        self.grade = GradeLevels(name="Grade 4", status=SectionStatusEnum.active)
        self.db.add(self.grade)
        self.db.flush()
        self.section = HI_SECTIONS(name="AVOCADO", grade_level_id=self.grade.id, teacher_id=self.teacher.id)
        self.same_name_section = HI_SECTIONS(
            name="AVOCADO",
            grade_level_id=self.grade.id,
            teacher_id=self.other_teacher.id,
        )
        self.db.add_all([self.section, self.same_name_section])
        self.db.flush()
        self.teacher_class = TeacherClass(
            teacher_id=self.teacher.id,
            class_name="Grade 4 - Avocado",
            subject="Science",
            grade_level_id=self.grade.id,
            section_id=self.section.id,
            student_count=0,
        )
        self.other_class = TeacherClass(
            teacher_id=self.other_teacher.id,
            class_name="Other Avocado",
            subject="Science",
            grade_level_id=self.grade.id,
            section_id=self.same_name_section.id,
            student_count=0,
        )
        self.db.add_all([self.teacher_class, self.other_class])
        self.db.flush()
        self.module = TeacherModule(
            teacher_id=self.teacher.id,
            class_id=self.teacher_class.id,
            title="Science",
            description="Grade 4 science",
            status="Published",
        )
        self.db.add(self.module)
        self.db.flush()
        self.topic_one = LearningTopic(module_id=self.module.id, title="Introduction", content="A", sort_order=1)
        self.duplicate_topic = LearningTopic(module_id=self.module.id, title="Introduction", content="B", sort_order=2)
        self.slide_marker = LearningTopic(module_id=self.module.id, title="--- Slide 3 ---", content="C", sort_order=3)
        self.topic_two = LearningTopic(module_id=self.module.id, title="Experiment", content="D", sort_order=4)
        self.db.add_all([self.topic_one, self.duplicate_topic, self.slide_marker, self.topic_two])
        self.db.flush()
        self.quiz = TeacherAssessment(
            teacher_id=self.teacher.id,
            class_id=self.teacher_class.id,
            module_id=self.module.id,
            assessment_type="quiz",
            title="Quiz 1",
            description="Quiz",
            questions=[{"prompt": "Q", "answer": "A"}] * 4,
        )
        self.activity = TeacherAssessment(
            teacher_id=self.teacher.id,
            class_id=self.teacher_class.id,
            assessment_type="activity",
            title="Activity 1",
            description="Activity",
            questions=[{"prompt": "Q", "answer": "A"}] * 2,
        )
        self.db.add_all([self.quiz, self.activity])
        self.db.flush()
        self.student_account, self.student = self._student("Learner One", "learner1", self.section)
        self.new_account, self.new_student = self._student("New Learner", "learner2", self.section)
        self.outside_account, self.outside_student = self._student(
            "Wrong Section",
            "outside",
            self.same_name_section,
        )
        self.db.commit()

    def test_opened_topic_persists_and_uses_visible_topic_total(self):
        self.assertEqual(
            _visible_topic_ids(self.module.id, self.db),
            [self.topic_one.id, self.topic_two.id],
        )

        result = update_topic_progress(
            request=None,
            module_id=self.module.id,
            topic_id=self.topic_one.id,
            status_value="in_progress",
            db=self.db,
            current_user=self.student_account,
        )
        self.assertEqual(result["total_topics"], 2)
        self.db.close()

        with self.Session() as reloaded:
            saved = reloaded.query(StudentTopicProgress).filter_by(
                student_id=self.student_account.id,
                topic_id=self.topic_one.id,
            ).one()
            self.assertEqual(saved.status, "in_progress")

    def test_teacher_summary_is_exactly_scoped_and_reports_all_progress(self):
        now = utc_now()
        self.db.add_all([
            StudentTopicProgress(
                student_id=self.student_account.id,
                module_id=self.module.id,
                topic_id=self.topic_one.id,
                status="completed",
                completed_at=now - timedelta(minutes=5),
            ),
            StudentTopicProgress(
                student_id=self.student_account.id,
                module_id=self.module.id,
                topic_id=self.topic_two.id,
                status="in_progress",
            ),
            StudentQuizProgress(
                student_id=self.student_account.id,
                module_id=self.module.id,
                assessment_id=self.quiz.id,
                status="completed",
                score=3,
                total=4,
                answers={"0": "A"},
                attempt_count=1,
                attempt_history=[],
                completed_at=now - timedelta(minutes=2),
            ),
            StudentQuizProgress(
                student_id=self.student_account.id,
                module_id=None,
                assessment_id=self.activity.id,
                status="completed",
                score=2,
                total=2,
                answers={"0": "A"},
                attempt_count=1,
                attempt_history=[],
                completed_at=now,
            ),
        ])
        self.db.flush()
        activity_progress = self.db.query(StudentQuizProgress).filter_by(
            student_id=self.student_account.id,
            assessment_id=self.activity.id,
        ).one()
        self.db.add(HandsignTutorialPractice(
            student_id=self.student_account.id,
            activity_id=self.activity.id,
            progress_id=activity_progress.id,
            canonical_word="TREE",
            attempt_scores=[70.0, 80.0, 90.0],
            highest_score=90.0,
            completed_at=now,
        ))
        self.db.commit()

        summary = _dashboard_progress_for_student(
            self.student,
            [self.teacher_class],
            self.db,
            self.teacher,
        )
        self.assertEqual(summary["overall_percent"], 75)
        self.assertEqual(summary["completed_tasks"], 3)
        self.assertEqual(summary["incomplete_tasks"], 1)
        self.assertEqual(summary["activities_completed"], 1)
        self.assertEqual(summary["activities_total"], 1)
        self.assertEqual(summary["activity_percent"], 100)
        self.assertEqual(summary["quizzes_completed"], 1)
        self.assertEqual(summary["quizzes_total"], 1)
        self.assertEqual(summary["quiz_average_percent"], 75)
        self.assertEqual(summary["handsign_practice_count"], 1)
        self.assertEqual(summary["handsign_best_score"], 90.0)
        self.assertEqual(summary["latest_assessment_title"], "Activity 1")

        records = list_teacher_student_records(
            request=None,
            class_id=self.teacher_class.id,
            assessment_type=None,
            status_filter=None,
            search=None,
            db=self.db,
            current_user=self.teacher,
        )
        self.assertEqual({record["student_name"] for record in records}, {"Learner One", "New Learner"})
        new_record = next(record for record in records if record["student_name"] == "New Learner")
        self.assertEqual(new_record["status"], "Not Started")
        self.assertEqual(
            {item["status"] for item in new_record["assessments"]},
            {"not_started"},
        )

    def test_retake_preserves_attempt_history_without_duplicate_progress(self):
        completed_at = utc_now()
        progress = StudentQuizProgress(
            student_id=self.student_account.id,
            module_id=self.module.id,
            assessment_id=self.quiz.id,
            status="completed",
            score=1,
            total=4,
            answers={"0": "B"},
            completed_at=completed_at,
            attempt_count=0,
            attempt_history=[],
        )
        self.db.add(progress)
        self.db.commit()
        progress_id = progress.id

        self.assertEqual(_reset_progress_for_retake(progress), 1)
        self.db.commit()
        self.assertEqual(progress.id, progress_id)
        self.assertEqual(progress.attempt_count, 1)
        self.assertEqual(len(progress.attempt_history), 1)
        self.assertEqual(progress.status, "in_progress")

        _complete_assessment_progress(progress, self.quiz, {"0": "A"}, "manual")
        self.db.commit()
        self.assertEqual(progress.attempt_count, 2)
        self.assertEqual(len(progress.attempt_history), 2)
        self.assertEqual(
            self.db.query(StudentQuizProgress).filter_by(
                student_id=self.student_account.id,
                assessment_id=self.quiz.id,
            ).count(),
            1,
        )


if __name__ == "__main__":
    unittest.main()
