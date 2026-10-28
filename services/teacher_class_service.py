from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.handsign_tutorial_practice import HandsignTutorialPractice
from models.learning_topic import LearningTopic
from models.student_progress import StudentTopicProgress
from models.student_profile import StudentProfile
from models.student_quiz_progress import StudentQuizProgress
from models.assessment_retake_request import AssessmentRetakeRequest
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from models.grade_levels import GradeLevels
from models.HI_sections import HI_SECTIONS
from schemas.teacher_class_schema import TeacherClassCreate
from services.academic_service import ALLOWED_GRADE_NAMES, get_grade_level_or_404, get_section_for_grade_or_400
from services.student_module_service import _visible_topics
from utils.enum import RoleEnum
from utils.utc_now import utc_now


def _ensure_teacher(current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def list_teacher_classes(request: Request, db: Session, current_user: Accounts):
    """Return classrooms created by the teacher from administrator-created sections."""
    _ensure_teacher(current_user)

    classes = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections),
        )
        .join(HI_SECTIONS, TeacherClass.section_id == HI_SECTIONS.id)
        .join(GradeLevels, TeacherClass.grade_level_id == GradeLevels.id)
        .filter(
            TeacherClass.teacher_id == current_user.id,
            HI_SECTIONS.teacher_id == current_user.id,
            GradeLevels.name.in_(ALLOWED_GRADE_NAMES),
        )
        .order_by(TeacherClass.created_at.desc())
        .all()
    )

    for teacher_class in classes:
        teacher_class.student_count = db.query(StudentProfile).filter(
            StudentProfile.section_id == teacher_class.section_id,
        ).count()
    return classes


def create_teacher_class(
    request: Request,
    teacher_class: TeacherClassCreate,
    db: Session,
    current_user: Accounts,
):
    """Create a teacher classroom using an existing administrator-created section."""
    _ensure_teacher(current_user)
    if teacher_class.section_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Choose an existing section for this class",
        )

    get_grade_level_or_404(teacher_class.grade_level_id, db)
    section = get_section_for_grade_or_400(
        teacher_class.section_id,
        teacher_class.grade_level_id,
        db,
    )
    if section.teacher_id and section.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This section is already assigned to another teacher",
        )

    existing = db.query(TeacherClass).filter(
        TeacherClass.teacher_id == current_user.id,
        TeacherClass.section_id == section.id,
        TeacherClass.subject == teacher_class.subject.strip(),
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a classroom for this section",
        )

    section.teacher_id = current_user.id
    classroom = TeacherClass(
        teacher_id=current_user.id,
        class_name=teacher_class.class_name.strip(),
        subject=teacher_class.subject.strip(),
        grade_level_id=teacher_class.grade_level_id,
        section_id=section.id,
        school_year=teacher_class.school_year.strip() if teacher_class.school_year else None,
        student_count=0,
    )
    db.add(classroom)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to create this classroom",
        )

    result = db.query(TeacherClass).options(
        joinedload(TeacherClass.grade_levels),
        joinedload(TeacherClass.sections),
    ).filter(TeacherClass.id == classroom.id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to load the created classroom",
        )
    result.student_count = db.query(StudentProfile).filter(
        StudentProfile.section_id == section.id,
    ).count()
    return result




def _get_assigned_section(class_id: int, db: Session, current_user: Accounts) -> HI_SECTIONS:
    """Resolve a section ID or legacy TeacherClass ID to a teacher-owned section."""
    section = (
        db.query(HI_SECTIONS)
        .filter(HI_SECTIONS.id == class_id, HI_SECTIONS.teacher_id == current_user.id)
        .first()
    )
    if section:
        return section

    teacher_class = (
        db.query(TeacherClass)
        .options(joinedload(TeacherClass.sections))
        .filter(TeacherClass.id == class_id, TeacherClass.teacher_id == current_user.id)
        .first()
    )
    if teacher_class and teacher_class.sections and teacher_class.sections.teacher_id == current_user.id:
        return teacher_class.sections

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned class not found")


def get_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    """Look up a teacher classroom, with section-ID compatibility for older clients."""
    _ensure_teacher(current_user)

    classroom = db.query(TeacherClass).options(
        joinedload(TeacherClass.grade_levels),
        joinedload(TeacherClass.sections),
    ).filter(
        TeacherClass.id == class_id,
        TeacherClass.teacher_id == current_user.id,
    ).first()
    if classroom:
        classroom.student_count = db.query(StudentProfile).filter(
            StudentProfile.section_id == classroom.section_id,
        ).count()
        return classroom

    section = _get_assigned_section(class_id, db, current_user)
    classroom = db.query(TeacherClass).options(
        joinedload(TeacherClass.grade_levels),
        joinedload(TeacherClass.sections),
    ).filter(
        TeacherClass.teacher_id == current_user.id,
        TeacherClass.section_id == section.id,
    ).first()
    if not classroom:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    classroom.student_count = db.query(StudentProfile).filter(
        StudentProfile.section_id == classroom.section_id,
    ).count()
    return classroom


def delete_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    """Teachers cannot delete sections — return 403."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sections cannot be deleted by teachers. Contact your administrator.",
    )


def list_class_students(request: Request, class_id: int, db: Session, current_user: Accounts):
    """Return students enrolled in the given assigned section."""
    _ensure_teacher(current_user)
    section = _get_assigned_section(class_id, db, current_user)

    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.grade_level), joinedload(StudentProfile.section))
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.section_id == section.id,
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
        .all()
    )
    return students


def get_teacher_dashboard_summary(request: Request, class_id: int | None, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    # Use admin-assigned hi_sections for student scoping
    if class_id is not None:
        assigned_sections = [_get_assigned_section(class_id, db, current_user)]
    else:
        assigned_sections = (
            db.query(HI_SECTIONS)
            .filter(HI_SECTIONS.teacher_id == current_user.id)
            .all()
        )

    if not assigned_sections:
        return {
            "total_students": 0,
            "active_learning_materials": 0,
            "average_quiz_score": 0,
            "student_progress": [],
        }

    section_ids = [sec.id for sec in assigned_sections]

    students = (
        db.query(StudentProfile)
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.section_id.in_(section_ids),
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
        .all()
    )
    student_ids = [s.account_id for s in students]

    # For quiz average, collect all teacher classes linked to these sections
    classes = (
        db.query(TeacherClass)
        .filter(
            TeacherClass.teacher_id == current_user.id,
            TeacherClass.section_id.in_(section_ids),
        )
        .all()
    )
    class_ids = [c.id for c in classes]
    published_module_count = db.query(TeacherModule).filter(
        TeacherModule.teacher_id == current_user.id,
        TeacherModule.status == "Published",
        TeacherModule.class_id.in_(class_ids),
    ).count() if class_ids else 0
    quiz_average = _average_quiz_score(student_ids, class_ids, db, current_user)

    student_progress = [
        _dashboard_progress_for_student(student, classes, db, current_user)
        for student in students
    ]

    return {
        "total_students": len(students),
        "active_learning_materials": published_module_count,
        "average_quiz_score": quiz_average,
        "student_progress": student_progress,
    }



def list_recent_activities(request: Request, limit: int, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    module_rows = (
        db.query(TeacherModule)
        .filter(TeacherModule.teacher_id == current_user.id)
        .order_by(TeacherModule.created_at.desc())
        .limit(limit)
        .all()
    )
    assessment_rows = (
        db.query(TeacherAssessment)
        .filter(
            TeacherAssessment.teacher_id == current_user.id,
            TeacherAssessment.assessment_type.in_(["quiz", "activity"]),
        )
        .order_by(TeacherAssessment.created_at.desc())
        .limit(limit)
        .all()
    )

    activities = []
    for module in module_rows:
        activities.append({
            "id": f"material-{module.id}",
            "text": f"Teacher uploaded a Learning Material: {module.title}",
            "occurred_at": module.created_at,
            "activity_type": "material",
        })
    for assessment in assessment_rows:
        label = "Quiz" if assessment.assessment_type == "quiz" else "Activity"
        activities.append({
            "id": f"{assessment.assessment_type}-{assessment.id}",
            "text": f"Teacher uploaded a {label}: {assessment.title}",
            "occurred_at": assessment.created_at,
            "activity_type": assessment.assessment_type,
        })

    activities.sort(key=lambda item: item["occurred_at"], reverse=True)
    return activities[:limit]


def _matching_student_query(teacher_class: TeacherClass, db: Session):
    return (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section)
        )
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.grade_level_id == teacher_class.grade_level_id,
            StudentProfile.section_id == teacher_class.section_id,
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
    )


def _count_matching_students(teacher_class: TeacherClass, db: Session):
    return _matching_student_query(teacher_class, db).count()


def _unique_students_for_classes(classes: list[TeacherClass], db: Session):
    section_ids = {teacher_class.section_id for teacher_class in classes}
    if not section_ids:
        return []

    return (
        db.query(StudentProfile)
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            Accounts.role == RoleEnum.student,
            StudentProfile.section_id.in_(section_ids),
        )
        .order_by(StudentProfile.name.asc())
        .all()
    )


def _average_quiz_score(student_ids: list[int], class_ids: list[int], db: Session, current_user: Accounts):
    if not student_ids:
        return 0
    module_ids = [
        row.id for row in db.query(TeacherModule.id)
        .filter(
            TeacherModule.teacher_id == current_user.id,
            TeacherModule.class_id.in_(class_ids),
            TeacherModule.status == "Published",
        )
        .all()
    ] if class_ids else []
    quiz_rows = (
        db.query(StudentQuizProgress.score, StudentQuizProgress.total)
        .join(TeacherAssessment, TeacherAssessment.id == StudentQuizProgress.assessment_id)
        .filter(
            TeacherAssessment.teacher_id == current_user.id,
            TeacherAssessment.assessment_type == "quiz",
            TeacherAssessment.module_id.in_(module_ids),
            StudentQuizProgress.student_id.in_(student_ids),
            StudentQuizProgress.status == "completed",
            StudentQuizProgress.total.isnot(None),
            StudentQuizProgress.total > 0,
        )
        .all()
    )
    if not quiz_rows:
        return 0
    percentages = [(row.score or 0) / row.total * 100 for row in quiz_rows]
    return round(sum(percentages) / len(percentages))


def _dashboard_progress_for_student(student: StudentProfile, classes: list[TeacherClass], db: Session, current_user: Accounts):
    matching_class_ids = [
        teacher_class.id for teacher_class in classes
        if teacher_class.grade_level_id == student.grade_level_id
        and teacher_class.section_id == student.section_id
    ]
    module_ids = [
        row.id for row in db.query(TeacherModule.id)
        .filter(
            TeacherModule.teacher_id == current_user.id,
            TeacherModule.class_id.in_(matching_class_ids),
            TeacherModule.status == "Published",
        )
        .all()
    ] if matching_class_ids else []
    topic_rows = db.query(LearningTopic).filter(
        LearningTopic.module_id.in_(module_ids)
    ).order_by(LearningTopic.module_id, LearningTopic.sort_order, LearningTopic.id).all() if module_ids else []
    topics_by_module: dict[int, list[LearningTopic]] = {}
    for topic in topic_rows:
        topics_by_module.setdefault(topic.module_id, []).append(topic)
    topic_ids = [
        topic.id
        for module_topics in topics_by_module.values()
        for topic in _visible_topics(module_topics)
    ]
    quizzes = db.query(TeacherAssessment).filter(
        TeacherAssessment.teacher_id == current_user.id,
        TeacherAssessment.module_id.in_(module_ids),
        TeacherAssessment.assessment_type == "quiz",
    ).all() if module_ids else []
    activities = db.query(TeacherAssessment).filter(
        TeacherAssessment.teacher_id == current_user.id,
        TeacherAssessment.class_id.in_(matching_class_ids),
        TeacherAssessment.assessment_type == "activity",
    ).all() if matching_class_ids else []
    quiz_ids = [assessment.id for assessment in quizzes]
    activity_ids = [assessment.id for assessment in activities]
    assessment_ids = quiz_ids + activity_ids
    assessments_by_id = {assessment.id: assessment for assessment in quizzes + activities}

    topic_progress = db.query(StudentTopicProgress).filter(
        StudentTopicProgress.student_id == student.account_id,
        StudentTopicProgress.topic_id.in_(topic_ids),
    ).all() if topic_ids else []
    assessment_progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == student.account_id,
        StudentQuizProgress.assessment_id.in_(assessment_ids),
    ).all() if assessment_ids else []
    progress_by_assessment = {item.assessment_id: item for item in assessment_progress}

    completed_topic_ids = {item.topic_id for item in topic_progress if item.status == "completed"}
    in_progress_topic_ids = {
        item.topic_id for item in topic_progress
        if item.status in {"started", "in_progress"}
    }
    completed_quiz_progress = [
        progress_by_assessment[item_id] for item_id in quiz_ids
        if item_id in progress_by_assessment and progress_by_assessment[item_id].status == "completed"
    ]
    completed_activity_progress = [
        progress_by_assessment[item_id] for item_id in activity_ids
        if item_id in progress_by_assessment and progress_by_assessment[item_id].status == "completed"
    ]
    completed_assessment_count = len(completed_quiz_progress) + len(completed_activity_progress)
    total_items = len(topic_ids) + len(assessment_ids)
    completed_items = len(completed_topic_ids) + completed_assessment_count
    overall_percent = round((completed_items / total_items) * 100) if total_items else 0
    activity_percent = _score_percent(completed_activity_progress)
    quiz_average_percent = _score_percent(completed_quiz_progress)

    latest_assessment_progress = max(
        assessment_progress,
        key=lambda item: item.completed_at or item.updated_at or item.started_at or utc_now(),
        default=None,
    )
    latest_assessment = assessments_by_id.get(latest_assessment_progress.assessment_id) if latest_assessment_progress else None
    latest_quiz_progress = max(
        (item for item in assessment_progress if item.assessment_id in quiz_ids),
        key=lambda item: item.completed_at or item.updated_at or item.started_at or utc_now(),
        default=None,
    )
    quiz_activity = _format_quiz_activity(latest_quiz_progress, db) if latest_quiz_progress else None

    handsign_progress = db.query(HandsignTutorialPractice).filter(
        HandsignTutorialPractice.student_id == student.account_id,
        HandsignTutorialPractice.activity_id.in_(activity_ids),
    ).all() if activity_ids else []
    activity_dates = [
        value for value in [
            *(item.updated_at for item in topic_progress),
            *(item.updated_at for item in assessment_progress),
            *(item.updated_at for item in handsign_progress),
        ] if value
    ]
    last_activity = max(activity_dates) if activity_dates else None
    status_value = "No Tasks" if not total_items else (
        "Not Started" if not completed_items and not in_progress_topic_ids and not assessment_progress
        else _progress_status_label(overall_percent)
    )
    return {
        "student_id": student.account_id,
        "student_name": student.name,
        "overall_percent": overall_percent,
        "activities_completed": len(completed_activity_progress),
        "activities_total": len(activity_ids),
        "activity_percent": activity_percent,
        "learning_materials_completed": len(completed_topic_ids),
        "learning_materials_in_progress": len(in_progress_topic_ids),
        "learning_materials_total": len(topic_ids),
        "quizzes_completed": len(completed_quiz_progress),
        "quizzes_total": len(quiz_ids),
        "quiz_average_percent": quiz_average_percent,
        "completed_tasks": completed_items,
        "incomplete_tasks": max(0, total_items - completed_items),
        "total_tasks": total_items,
        "handsign_practice_count": len(handsign_progress),
        "handsign_best_score": max((item.highest_score for item in handsign_progress), default=None),
        "latest_assessment_title": latest_assessment.title if latest_assessment else None,
        "latest_assessment_type": latest_assessment.assessment_type if latest_assessment else None,
        "latest_assessment_status": latest_assessment_progress.status if latest_assessment_progress else None,
        "latest_assessment_score": latest_assessment_progress.score if latest_assessment_progress else None,
        "latest_assessment_total": latest_assessment_progress.total if latest_assessment_progress else None,
        "latest_assessment_completed_at": latest_assessment_progress.completed_at if latest_assessment_progress else None,
        "status": status_value,
        "last_activity": last_activity,
        "quiz_activity": quiz_activity,
    }


def _score_percent(progress_rows: list[StudentQuizProgress]) -> int:
    total = sum(item.total or 0 for item in progress_rows)
    if not total:
        return 0
    return round(sum(item.score or 0 for item in progress_rows) / total * 100)


def _format_quiz_activity(progress: StudentQuizProgress, db: Session):
    assessment = db.query(TeacherAssessment).filter(TeacherAssessment.id == progress.assessment_id).first()
    if not assessment:
        return None
    if progress.total:
        source = " Auto-submitted" if progress.submission_type == "timed_out" else ""
        return f"{assessment.title}: {progress.score or 0}/{progress.total}{source}"
    return assessment.title


def _progress_status_label(percent: int) -> str:
    if percent <= 50:
        return "Needs Guidance"
    if percent <= 74:
        return "Keep Improving"
    if percent <= 89:
        return "Good Progress"
    return "Excellent"


def list_teacher_student_records(
    request: Request,
    class_id: int | None,
    assessment_type: str | None,
    status_filter: str | None,
    search: str | None,
    db: Session,
    current_user: Accounts,
):
    _ensure_teacher(current_user)
    if class_id is None:
        classes = (
            db.query(TeacherClass)
            .options(joinedload(TeacherClass.grade_levels), joinedload(TeacherClass.sections))
            .join(HI_SECTIONS, TeacherClass.section_id == HI_SECTIONS.id)
            .join(GradeLevels, TeacherClass.grade_level_id == GradeLevels.id)
            .filter(
                TeacherClass.teacher_id == current_user.id,
                HI_SECTIONS.teacher_id == current_user.id,
                GradeLevels.name.in_(ALLOWED_GRADE_NAMES),
            )
            .all()
        )
    else:
        section = _get_assigned_section(class_id, db, current_user)
        classes = (
            db.query(TeacherClass)
            .options(joinedload(TeacherClass.grade_levels), joinedload(TeacherClass.sections))
            .filter(
                TeacherClass.teacher_id == current_user.id,
                TeacherClass.section_id == section.id,
            )
            .all()
        )

    students = _unique_students_for_classes(classes, db)
    if search:
        query = search.strip().lower()
        students = [student for student in students if query in (student.name or '').lower()]

    class_ids = [teacher_class.id for teacher_class in classes]
    student_ids = [student.account_id for student in students]
    if not class_ids or not student_ids:
        return []

    module_ids = [
        row.id for row in db.query(TeacherModule.id)
        .filter(
            TeacherModule.teacher_id == current_user.id,
            TeacherModule.class_id.in_(class_ids),
            TeacherModule.status == "Published",
        )
        .all()
    ]
    assessment_filters = [TeacherAssessment.teacher_id == current_user.id]
    activity_filter = (
        (TeacherAssessment.assessment_type == 'activity')
        & (TeacherAssessment.class_id.in_(class_ids))
    )
    quiz_filter = (
        (TeacherAssessment.assessment_type == 'quiz')
        & (TeacherAssessment.module_id.in_(module_ids))
    ) if module_ids else None
    assessment_filters.append(activity_filter | quiz_filter if quiz_filter is not None else activity_filter)
    if assessment_type in {'activity', 'quiz'}:
        assessment_filters.append(TeacherAssessment.assessment_type == assessment_type)

    assessments = (
        db.query(TeacherAssessment)
        .filter(*assessment_filters)
        .order_by(TeacherAssessment.created_at.desc())
        .all()
    )
    assessment_ids = [assessment.id for assessment in assessments]
    assessments_by_id = {assessment.id: assessment for assessment in assessments}

    progress_rows = (
        db.query(StudentQuizProgress)
        .filter(
            StudentQuizProgress.student_id.in_(student_ids),
            StudentQuizProgress.assessment_id.in_(assessment_ids),
        )
        .all()
    ) if assessment_ids else []
    progress_by_student: dict[int, dict[int, StudentQuizProgress]] = {}
    for progress in progress_rows:
        progress_by_student.setdefault(progress.student_id, {})[progress.assessment_id] = progress

    handsign_rows = []
    if assessment_ids:
        try:
            handsign_rows = (
                db.query(HandsignTutorialPractice)
                .filter(
                    HandsignTutorialPractice.student_id.in_(student_ids),
                    HandsignTutorialPractice.activity_id.in_(assessment_ids),
                )
                .order_by(HandsignTutorialPractice.completed_at.desc().nullslast())
                .all()
            )
        except Exception:
            db.rollback()
            handsign_rows = []
    handsign_by_student: dict[int, list[HandsignTutorialPractice]] = {}
    for practice in handsign_rows:
        handsign_by_student.setdefault(practice.student_id, []).append(practice)

    retake_rows = []
    if assessment_ids and student_ids:
        retake_rows = (
            db.query(AssessmentRetakeRequest)
            .filter(
                AssessmentRetakeRequest.teacher_id == current_user.id,
                AssessmentRetakeRequest.student_id.in_(student_ids),
                AssessmentRetakeRequest.assessment_id.in_(assessment_ids),
            )
            .order_by(AssessmentRetakeRequest.created_at.desc())
            .all()
        )
    retake_by_student_assessment: dict[tuple[int, int], AssessmentRetakeRequest] = {}
    for retake in retake_rows:
        key = (retake.student_id, retake.assessment_id)
        if key not in retake_by_student_assessment:
            retake_by_student_assessment[key] = retake

    records = []
    for student in students:
        summary = _dashboard_progress_for_student(student, classes, db, current_user)
        assessment_records = []
        student_progress = progress_by_student.get(student.account_id, {})
        for assessment in assessments:
            progress = student_progress.get(assessment.id)
            expected_answers = [
                str(question.get('answer') or '').strip()
                for question in (assessment.questions or [])
                if str(question.get('answer') or '').strip()
            ]
            retake_access = retake_by_student_assessment.get((student.account_id, assessment.id))
            attempt_history = list(progress.attempt_history or []) if progress else []
            attempt_count = (progress.attempt_count or len(attempt_history)) if progress else 0
            if progress and progress.status == 'completed' and not attempt_history:
                attempt_count = max(1, attempt_count)
                attempt_history = [{
                    'attempt_number': attempt_count,
                    'score': progress.score,
                    'total': progress.total,
                    'answers': progress.answers or {},
                    'submission_type': progress.submission_type,
                    'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                }]
            assessment_records.append({
                'assessment_id': assessment.id,
                'title': assessment.title,
                'assessment_type': assessment.assessment_type,
                'expected_answers': expected_answers,
                'status': progress.status if progress else 'not_started',
                'score': progress.score if progress else None,
                'total': progress.total if progress else len(assessment.questions or []),
                'answers': progress.answers or {} if progress else {},
                'completed_at': progress.completed_at if progress else None,
                'submission_type': progress.submission_type if progress else None,
                'retake_status': retake_access.status if retake_access else None,
                'attempt_count': attempt_count,
                'attempt_history': attempt_history,
            })

        assessment_records.sort(
            key=lambda item: item['completed_at'] or assessments_by_id[item['assessment_id']].created_at,
            reverse=True,
        )

        if status_filter and status_filter != 'all':
            normalized_status = status_filter.strip().lower().replace('_', ' ')
            if normalized_status not in {
                summary['status'].lower(),
                *(item['status'].lower().replace('_', ' ') for item in assessment_records),
            }:
                continue

        handsign_records = []
        for practice in handsign_by_student.get(student.account_id, []):
            activity = assessments_by_id.get(practice.activity_id)
            handsign_records.append({
                'id': practice.id,
                'activity_id': practice.activity_id,
                'activity_title': activity.title if activity else None,
                'word': practice.canonical_word,
                'attempt_scores': practice.attempt_scores or [],
                'highest_score': practice.highest_score,
                'completed_at': practice.completed_at,
            })

        records.append({
            **summary,
            'grade_level': student.grade_level.name if student.grade_level else None,
            'section': student.section.name if student.section else None,
            'assessments': assessment_records,
            'handsign_practice': handsign_records,
        })

    return records


def _resolve_manual_section(teacher_class: TeacherClassCreate, db: Session):
    if teacher_class.section_id:
        return get_section_for_grade_or_400(teacher_class.section_id, teacher_class.grade_level_id, db)

    if not teacher_class.section:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Section is required",
        )

    section_name = _normalize_manual_section(teacher_class.section)
    existing_section = (
        db.query(HI_SECTIONS)
        .filter(
            HI_SECTIONS.grade_level_id == teacher_class.grade_level_id,
            func.lower(func.trim(HI_SECTIONS.name)) == section_name.lower(),
        )
        .first()
    )
    if existing_section:
        return existing_section

    new_section = HI_SECTIONS(
        name=section_name,
        grade_level_id=teacher_class.grade_level_id,
    )
    db.add(new_section)
    db.flush()
    return new_section


def _normalize_manual_section(section: str):
    return " ".join(section.strip().split()).upper()


