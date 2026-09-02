from fastapi import HTTPException, Request, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.handsign_tutorial_practice import HandsignTutorialPractice
from models.learning_topic import LearningTopic
from models.student_progress import StudentTopicProgress
from models.student_profile import StudentProfile
from models.student_quiz_progress import StudentQuizProgress
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from models.grade_levels import GradeLevels
from models.HI_sections import HI_SECTIONS
from schemas.teacher_class_schema import TeacherClassCreate
from services.academic_service import get_grade_level_or_404, get_section_for_grade_or_400
from utils.enum import RoleEnum
from utils.utc_now import utc_now


def _ensure_teacher(current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def list_teacher_classes(request: Request, db: Session, current_user: Accounts):
    """Return hi_sections that the admin has assigned to this teacher."""
    _ensure_teacher(current_user)

    assigned_sections = (
        db.query(HI_SECTIONS)
        .options(
            joinedload(HI_SECTIONS.grade_level),
        )
        .filter(HI_SECTIONS.teacher_id == current_user.id)
        .order_by(HI_SECTIONS.grade_level_id.asc(), HI_SECTIONS.name.asc())
        .all()
    )

    result = []
    for sec in assigned_sections:
        student_count = (
            db.query(StudentProfile)
            .filter(StudentProfile.section_id == sec.id)
            .count()
        )
        result.append({
            "id": sec.id,
            "class_name": f"{sec.grade_level.name if sec.grade_level else 'Grade'} - {sec.name}",
            "subject": "Science",
            "grade_levels": {
                "id": sec.grade_level_id,
                "name": sec.grade_level.name if sec.grade_level else "",
            },
            "sections": {
                "id": sec.id,
                "name": sec.name,
                "grade_level_id": sec.grade_level_id,
            },
            "school_year": None,
            "student_count": student_count,
            "teacher_id": current_user.id,
            "created_at": utc_now,
            "updated_at": utc_now,
        })
    return result


def create_teacher_class(request: Request, teacher_class, db: Session, current_user: Accounts):
    """Teachers cannot create official sections. Sections are assigned by the Administrator."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sections are created and assigned by the Administrator. Please contact your Administrator to be assigned to a section.",
    )




def get_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    """Look up an admin-assigned hi_section by id, verifying teacher ownership."""
    _ensure_teacher(current_user)

    section = (
        db.query(HI_SECTIONS)
        .options(joinedload(HI_SECTIONS.grade_level))
        .filter(HI_SECTIONS.id == class_id, HI_SECTIONS.teacher_id == current_user.id)
        .first()
    )

    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned class not found")

    return section


def delete_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    """Teachers cannot delete sections — return 403."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Sections cannot be deleted by teachers. Contact your administrator.",
    )


def list_class_students(request: Request, class_id: int, db: Session, current_user: Accounts):
    """Return students enrolled in the given assigned section."""
    _ensure_teacher(current_user)

    section = (
        db.query(HI_SECTIONS)
        .filter(HI_SECTIONS.id == class_id, HI_SECTIONS.teacher_id == current_user.id)
        .first()
    )
    if not section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assigned class not found")

    students = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.grade_level), joinedload(StudentProfile.section))
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.section_id == class_id,
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
        .all()
    )
    return students


def get_teacher_dashboard_summary(request: Request, class_id: int | None, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    # Use admin-assigned hi_sections for student scoping
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

    published_module_count = db.query(TeacherModule).filter(
        TeacherModule.teacher_id == current_user.id,
        TeacherModule.status == "Published",
    ).count()

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
    section_name = teacher_class.sections.name if teacher_class.sections else ""
    return (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section)
        )
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .join(HI_SECTIONS, StudentProfile.section_id == HI_SECTIONS.id)
        .filter(
            StudentProfile.grade_level_id == teacher_class.grade_level_id,
            func.lower(func.trim(HI_SECTIONS.name)) == section_name.strip().lower(),
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
    )


def _count_matching_students(teacher_class: TeacherClass, db: Session):
    return _matching_student_query(teacher_class, db).count()


def _unique_students_for_classes(classes: list[TeacherClass], db: Session):
    filters = []
    for teacher_class in classes:
        section_name = teacher_class.sections.name if teacher_class.sections else ""
        filters.append(
            (
                StudentProfile.grade_level_id == teacher_class.grade_level_id
            ) & (
                func.lower(func.trim(HI_SECTIONS.name)) == section_name.strip().lower()
            )
        )
    if not filters:
        return []

    return (
        db.query(StudentProfile)
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .join(HI_SECTIONS, StudentProfile.section_id == HI_SECTIONS.id)
        .filter(Accounts.role == RoleEnum.student, or_(*filters))
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
    if not matching_class_ids:
        total_items = 0
        completed_items = 0
        topic_ids = []
        activity_ids = []
        completed_topic_ids = set()
        in_progress_topic_ids = set()
        completed_activity_ids = set()
        activity_question_total = 0
        activity_correct_total = 0
        last_activity = None
        quiz_activity = None
    else:
        module_ids = [
            row.id for row in db.query(TeacherModule.id)
            .filter(
                TeacherModule.teacher_id == current_user.id,
                TeacherModule.class_id.in_(matching_class_ids),
                TeacherModule.status == "Published",
            )
            .all()
        ]
        topic_ids = [
            row.id for row in db.query(LearningTopic.id)
            .filter(LearningTopic.module_id.in_(module_ids))
            .all()
        ] if module_ids else []
        quiz_ids = [
            row.id for row in db.query(TeacherAssessment.id)
            .filter(
                TeacherAssessment.teacher_id == current_user.id,
                TeacherAssessment.module_id.in_(module_ids),
                TeacherAssessment.assessment_type == "quiz",
            )
            .all()
        ] if module_ids else []
        activity_ids = [
            row.id for row in db.query(TeacherAssessment.id)
            .filter(
                TeacherAssessment.teacher_id == current_user.id,
                TeacherAssessment.class_id.in_(matching_class_ids),
                TeacherAssessment.assessment_type == "activity",
            )
            .all()
        ]

        topic_progress = db.query(StudentTopicProgress).filter(
            StudentTopicProgress.student_id == student.account_id,
            StudentTopicProgress.topic_id.in_(topic_ids),
        ).all() if topic_ids else []
        quiz_progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == student.account_id,
            StudentQuizProgress.assessment_id.in_(quiz_ids),
        ).all() if quiz_ids else []
        activity_progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == student.account_id,
            StudentQuizProgress.assessment_id.in_(activity_ids),
        ).all() if activity_ids else []

        completed_topic_ids = {item.topic_id for item in topic_progress if item.status == "completed"}
        in_progress_topic_ids = {item.topic_id for item in topic_progress if item.status in {"started", "in_progress"}}
        completed_quiz_ids = {item.assessment_id for item in quiz_progress if item.status == "completed"}
        completed_activity_ids = {item.assessment_id for item in activity_progress if item.status == "completed"}
        activity_question_total = sum(
            len(assessment.questions or [])
            for assessment in db.query(TeacherAssessment)
            .filter(
                TeacherAssessment.id.in_(activity_ids),
                TeacherAssessment.assessment_type == "activity",
            )
            .all()
        ) if activity_ids else 0
        activity_correct_total = sum(item.score or 0 for item in activity_progress if item.status == "completed")
        total_items = len(topic_ids) + len(quiz_ids) + len(activity_ids)
        completed_items = len(completed_topic_ids) + len(completed_quiz_ids) + len(completed_activity_ids)
        activity_dates = [item.updated_at for item in topic_progress + quiz_progress + activity_progress if item.updated_at]
        last_activity = max(activity_dates) if activity_dates else None
        latest_quiz_progress = max(
            (item for item in quiz_progress if item.updated_at),
            key=lambda item: item.updated_at,
            default=None,
        )
        quiz_activity = _format_quiz_activity(latest_quiz_progress, db) if latest_quiz_progress else None

    status_percent = round((completed_items / total_items) * 100) if total_items else 0
    learning_material_percent = round((len(completed_topic_ids) / len(topic_ids)) * 100) if topic_ids else 0
    activity_percent = round((activity_correct_total / activity_question_total) * 100) if activity_question_total else 0
    status_value = "Complete" if total_items and completed_items == total_items else "Needs Help" if status_percent < 50 else "In Progress"
    return {
        "student_id": student.account_id,
        "student_name": student.name,
        "overall_percent": learning_material_percent,
        "activities_completed": activity_correct_total,
        "activities_total": activity_question_total,
        "activity_percent": activity_percent,
        "learning_materials_completed": len(completed_topic_ids),
        "learning_materials_in_progress": len(in_progress_topic_ids),
        "learning_materials_total": len(topic_ids),
        "status": status_value,
        "last_activity": last_activity,
        "quiz_activity": quiz_activity,
    }


def _format_quiz_activity(progress: StudentQuizProgress, db: Session):
    assessment = db.query(TeacherAssessment).filter(TeacherAssessment.id == progress.assessment_id).first()
    if not assessment:
        return None
    if progress.total:
        source = " Auto-submitted" if progress.submission_type == "timed_out" else ""
        return f"{assessment.title}: {progress.score or 0}/{progress.total}{source}"
    return assessment.title


def list_teacher_classes(request: Request, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    classes = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections),
        )
        .join(GradeLevels, TeacherClass.grade_level_id == GradeLevels.id)
        .join(HI_SECTIONS, TeacherClass.section_id == HI_SECTIONS.id)
        .filter(TeacherClass.teacher_id == current_user.id)
        .order_by(TeacherClass.created_at.desc())
        .all()
    )
    for teacher_class in classes:
        teacher_class.student_count = _count_matching_students(teacher_class, db)
    return classes


def create_teacher_class(request: Request, teacher_class: TeacherClassCreate, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    grade_level = get_grade_level_or_404(teacher_class.grade_level_id, db)
    section = _resolve_manual_section(teacher_class, db)

    new_teacher_class = TeacherClass(
        teacher_id=current_user.id,
        class_name=teacher_class.class_name.strip(),
        subject=teacher_class.subject.strip(),
        grade_level_id=teacher_class.grade_level_id,
        section_id=section.id,
        school_year=teacher_class.school_year.strip() if teacher_class.school_year else None,
        student_count=0,
    )

    db.add(new_teacher_class)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class already exists for this teacher, subject, grade level, and section",
        )

    db.refresh(new_teacher_class)
    new_teacher_class.student_count = _count_matching_students(new_teacher_class, db)

    result = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections),
        )
        .filter(TeacherClass.id == new_teacher_class.id)
        .first()
    )

    if not result:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to load created class")

    result.student_count = _count_matching_students(result, db)
    return result


def get_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    teacher_class = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections),
        )
        .join(GradeLevels, TeacherClass.grade_level_id == GradeLevels.id)
        .join(HI_SECTIONS, TeacherClass.section_id == HI_SECTIONS.id)
        .filter(TeacherClass.id == class_id, TeacherClass.teacher_id == current_user.id)
        .first()
    )

    if not teacher_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    teacher_class.student_count = _count_matching_students(teacher_class, db)
    return teacher_class


def delete_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user,
    )

    db.delete(teacher_class)
    db.commit()

    return {"detail": "Class deleted successfully"}


def list_class_students(request: Request, class_id: int, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user,
    )

    return _matching_student_query(teacher_class, db).all()


def get_teacher_dashboard_summary(request: Request, class_id: int | None, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    if class_id is None:
        classes = (
            db.query(TeacherClass)
            .filter(TeacherClass.teacher_id == current_user.id)
            .all()
        )
    else:
        classes = [get_teacher_class(request=request, class_id=class_id, db=db, current_user=current_user)]

    students = _unique_students_for_classes(classes, db)
    student_ids = [student.account_id for student in students]
    class_ids = [teacher_class.id for teacher_class in classes]

    module_count_filters = [
        TeacherModule.teacher_id == current_user.id,
        TeacherModule.status == "Published",
    ]
    if class_id is not None:
        module_count_filters.append(TeacherModule.class_id == class_id)
    published_module_count = db.query(TeacherModule).filter(*module_count_filters).count()

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
            .filter(TeacherClass.teacher_id == current_user.id)
            .all()
        )
    else:
        classes = [get_teacher_class(request=request, class_id=class_id, db=db, current_user=current_user)]

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
        .filter(TeacherModule.teacher_id == current_user.id, TeacherModule.class_id.in_(class_ids))
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
    progress_by_student: dict[int, list[StudentQuizProgress]] = {}
    for progress in progress_rows:
        progress_by_student.setdefault(progress.student_id, []).append(progress)

    handsign_rows = (
        db.query(HandsignTutorialPractice)
        .filter(
            HandsignTutorialPractice.student_id.in_(student_ids),
            HandsignTutorialPractice.activity_id.in_(assessment_ids),
        )
        .order_by(HandsignTutorialPractice.completed_at.desc().nullslast())
        .all()
    ) if assessment_ids else []
    handsign_by_student: dict[int, list[HandsignTutorialPractice]] = {}
    for practice in handsign_rows:
        handsign_by_student.setdefault(practice.student_id, []).append(practice)

    records = []
    for student in students:
        summary = _dashboard_progress_for_student(student, classes, db, current_user)
        assessment_records = []
        for progress in sorted(progress_by_student.get(student.account_id, []), key=lambda item: item.updated_at, reverse=True):
            assessment = assessments_by_id.get(progress.assessment_id)
            if not assessment:
                continue
            expected_answers = [
                str(question.get('answer') or '').strip()
                for question in (assessment.questions or [])
                if str(question.get('answer') or '').strip()
            ]
            assessment_records.append({
                'assessment_id': assessment.id,
                'title': assessment.title,
                'assessment_type': assessment.assessment_type,
                'expected_answers': expected_answers,
                'status': progress.status,
                'score': progress.score,
                'total': progress.total,
                'answers': progress.answers or {},
                'completed_at': progress.completed_at,
                'submission_type': progress.submission_type,
            })

        if status_filter and status_filter != 'all':
            normalized_status = status_filter.strip().lower().replace('_', ' ')
            if normalized_status not in {summary['status'].lower(), *(item['status'].lower().replace('_', ' ') for item in assessment_records)}:
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


