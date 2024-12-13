from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException
from .utils import get_password_hash
from . import schemas

async def get_user(db: AsyncSession, user_id: int):
    query = text("""
        SELECT user_id, first_name, last_name, email, phone, role_id, created_at
        FROM users
        WHERE user_id = :user_id
        LIMIT 1;
    """)
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()
    if row:
        return {
            "user_id": row.user_id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "phone": row.phone,
            "role_id": row.role_id,
            "created_at": row.created_at
        }
    return None

async def get_user_by_email(db: AsyncSession, email: str):
    query = text("""
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, u.role_id, u.created_at,
               a.auth_id, a.password_hash, a.salt
        FROM users AS u
        LEFT JOIN authentication AS a ON a.user_id = u.user_id
        WHERE u.email = :email
        LIMIT 1;
    """)
    result = await db.execute(query, {"email": email})
    row = result.fetchone()
    if row:
        return {
            "user_id": row.user_id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "phone": row.phone,
            "role_id": row.role_id,
            "created_at": row.created_at,
            "auth": {
                "auth_id": row.auth_id,
                "password_hash": row.password_hash,
                "salt": row.salt
            }
        }
    return None

async def get_user_by_phone(db: AsyncSession, phone: str):
    query = text("""
        SELECT u.user_id, u.first_name, u.last_name, u.email, u.phone, u.role_id, u.created_at,
               a.auth_id, a.password_hash, a.salt
        FROM users AS u
        LEFT JOIN authentication AS a ON a.user_id = u.user_id
        WHERE u.phone = :phone
        LIMIT 1;
    """)
    result = await db.execute(query, {"phone": phone})
    row = result.fetchone()
    if row:
        return {
            "user_id": row.user_id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "phone": row.phone,
            "role_id": row.role_id,
            "created_at": row.created_at,
            "auth": {
                "auth_id": row.auth_id,
                "password_hash": row.password_hash,
                "salt": row.salt
            }
        }
    return None

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)

    insert_user_query = text("""
        INSERT INTO users (first_name, last_name, email, phone, role_id, created_at)
        VALUES (:first_name, :last_name, :email, :phone, :role_id, NOW())
        RETURNING user_id, first_name, last_name, email, phone, role_id, created_at;
    """)

    result_user = await db.execute(insert_user_query, {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "role_id": user.role_id
    })
    db_user = result_user.fetchone()
    if not db_user:
        raise HTTPException(status_code=500, detail="Не удалось создать пользователя")

    insert_auth_query = text("""
        INSERT INTO authentication (user_id, password_hash, salt)
        VALUES (:user_id, :password_hash, 'not_used_with_bcrypt')
        RETURNING auth_id;
    """)

    await db.execute(insert_auth_query, {
        "user_id": db_user.user_id,
        "password_hash": hashed_password
    })

    await db.commit()

    return {
        "user_id": db_user.user_id,
        "first_name": db_user.first_name,
        "last_name": db_user.last_name,
        "email": db_user.email,
        "phone": db_user.phone,
        "role_id": db_user.role_id,
        "created_at": db_user.created_at
    }

async def get_current_user_from_db(db: AsyncSession, user_id: int):
    return await get_user(db, user_id)

async def create_tutor(db: AsyncSession, tutor: schemas.TutorCreate):
    query = text("""
        INSERT INTO tutors (user_id, description, experience, rating)
        VALUES (:user_id, :description, :experience, 0.00)
        RETURNING tutor_id, user_id, description, experience, rating;
    """)
    result = await db.execute(query, {
        "user_id": tutor.user_id,
        "description": tutor.description,
        "experience": tutor.experience
    })
    row = result.fetchone()
    await db.commit()
    if row:
        return {
            "tutor_id": row.tutor_id,
            "user_id": row.user_id,
            "description": row.description,
            "experience": row.experience,
            "rating": float(row.rating)
        }
    return None

async def get_tutor(db: AsyncSession, tutor_id: int):
    query = text("""
        SELECT tutor_id, user_id, description, experience, rating
        FROM tutors
        WHERE tutor_id = :tutor_id
        LIMIT 1;
    """)
    result = await db.execute(query, {"tutor_id": tutor_id})
    row = result.fetchone()
    if row:
        return {
            "tutor_id": row.tutor_id,
            "user_id": row.user_id,
            "description": row.description,
            "experience": row.experience,
            "rating": float(row.rating)
        }
    return None

async def get_tutors(db: AsyncSession):
    query = text("""
        SELECT tutor_id, user_id, description, experience, rating
        FROM tutors;
    """)
    result = await db.execute(query)
    rows = result.fetchall()
    tutors = []
    for row in rows:
        tutors.append({
            "tutor_id": row.tutor_id,
            "user_id": row.user_id,
            "description": row.description,
            "experience": row.experience,
            "rating": float(row.rating)
        })
    return tutors

async def create_student(db: AsyncSession, student: schemas.StudentCreate):
    query = text("""
        INSERT INTO students (user_id, education_level, interests)
        VALUES (:user_id, :education_level, :interests)
        RETURNING student_id, user_id, education_level, interests;
    """)
    result = await db.execute(query, {
        "user_id": student.user_id,
        "education_level": student.education_level,
        "interests": student.interests
    })
    row = result.fetchone()
    await db.commit()
    if row:
        return {
            "student_id": row.student_id,
            "user_id": row.user_id,
            "education_level": row.education_level,
            "interests": row.interests
        }
    return None

async def get_student(db: AsyncSession, student_id: int):
    query = text("""
        SELECT student_id, user_id, education_level, interests
        FROM students
        WHERE student_id = :student_id
        LIMIT 1;
    """)
    result = await db.execute(query, {"student_id": student_id})
    row = result.fetchone()
    if row:
        return {
            "student_id": row.student_id,
            "user_id": row.user_id,
            "education_level": row.education_level,
            "interests": row.interests
        }
    return None




async def get_subject_by_id(db: AsyncSession, subject_id: int):
    query = text("""
        SELECT subject_id, subject_name, description
        FROM subjects
        WHERE subject_id = :subject_id
        LIMIT 1;
    """)
    res = await db.execute(query, {"subject_id": subject_id})
    row = res.fetchone()
    if row:
        return {
            "subject_id": row.subject_id,
            "subject_name": row.subject_name,
            "description": row.description
        }
    return None


async def create_lesson(db: AsyncSession, lesson: schemas.LessonCreate):
    query = text("""
        INSERT INTO lessons (tutor_id, student_id, subject_id, lesson_date, lesson_time, status)
        VALUES (:tutor_id, :student_id, :subject_id, :lesson_date, :lesson_time, :status)
        RETURNING lesson_id, tutor_id, student_id, subject_id, lesson_date, lesson_time, status;
    """)
    result = await db.execute(query, {
        "tutor_id": lesson.tutor_id,
        "student_id": lesson.student_id,
        "subject_id": lesson.subject_id,
        "lesson_date": lesson.lesson_date,
        "lesson_time": lesson.lesson_time,
        "status": lesson.status or "scheduled"
    })
    row = result.fetchone()
    await db.commit()
    if row:
        return {
            "lesson_id": row.lesson_id,
            "tutor_id": row.tutor_id,
            "student_id": row.student_id,
            "subject_id": row.subject_id,
            "lesson_date": row.lesson_date,
            "lesson_time": row.lesson_time,
            "status": row.status
        }
    return None

async def get_lessons_by_student(db: AsyncSession, student_id: int):
    query = text("""
        SELECT 
            lesson_id,
            tutor_id,
            student_id,
            subject_id,
            lesson_date,
            lesson_time,
            status
        FROM lessons
        WHERE student_id = :student_id
        ORDER BY lesson_date, lesson_time;
    """)
    result = await db.execute(query, {"student_id": student_id})
    rows = result.fetchall()

    lessons = []
    for row in rows:
        lessons.append({
            "lesson_id": row.lesson_id,
            "tutor_id": row.tutor_id,
            "student_id": row.student_id,
            "subject_id": row.subject_id,
            "lesson_date": row.lesson_date,
            "lesson_time": row.lesson_time,
            "status": row.status
        })
    return lessons





async def get_lessons_by_tutor(db: AsyncSession, tutor_id: int):
    query = text("""
        SELECT lesson_id, tutor_id, student_id, subject_id, lesson_date, lesson_time, status
        FROM lessons
        WHERE tutor_id = :tutor_id
        ORDER BY lesson_date, lesson_time;
    """)
    result = await db.execute(query, {"tutor_id": tutor_id})
    rows = result.fetchall()
    return [
        {
            "lesson_id": row.lesson_id,
            "tutor_id": row.tutor_id,
            "student_id": row.student_id,
            "subject_id": row.subject_id,
            "lesson_date": row.lesson_date,
            "lesson_time": row.lesson_time,
            "status": row.status,
        }
        for row in rows
    ]


async def create_feedback(db: AsyncSession, feedback: schemas.FeedbackCreate):
    check_lesson_query = text("""
        SELECT lesson_id 
        FROM lessons
        WHERE lesson_id = :lesson_id AND tutor_id = :tutor_id AND student_id = :student_id
        LIMIT 1;
    """)
    check_res = await db.execute(check_lesson_query, {
        "lesson_id": feedback.lesson_id,
        "tutor_id": feedback.tutor_id,
        "student_id": feedback.student_id
    })
    lesson_row = check_res.fetchone()
    if not lesson_row:
        raise HTTPException(status_code=400, detail="Указанный урок не найден или не соответствует преподавателю/ученику.")

    insert_feedback_query = text("""
        INSERT INTO feedbacks (lesson_id, tutor_id, rating, comment)
        VALUES (:lesson_id, :tutor_id, :rating, :comment)
        RETURNING feedback_id, lesson_id, tutor_id, rating, comment;
    """)
    result = await db.execute(insert_feedback_query, {
        "lesson_id": feedback.lesson_id,
        "tutor_id": feedback.tutor_id,
        "rating": feedback.rating,
        "comment": feedback.comment
    })
    db_feedback = result.fetchone()
    await db.commit()

    if db_feedback:
        return {
            "feedback_id": db_feedback.feedback_id,
            "lesson_id": db_feedback.lesson_id,
            "tutor_id": db_feedback.tutor_id,
            "rating": db_feedback.rating,
            "comment": db_feedback.comment
        }
    return None


async def get_feedbacks_by_tutor(db: AsyncSession, tutor_id: int):
    query = text("""
        SELECT feedback_id, lesson_id, tutor_id, rating, comment
        FROM feedbacks
        WHERE tutor_id = :tutor_id
        ORDER BY feedback_id DESC;
    """)
    result = await db.execute(query, {"tutor_id": tutor_id})
    rows = result.fetchall()
    feedbacks = []
    for row in rows:
        feedbacks.append({
            "feedback_id": row.feedback_id,
            "lesson_id": row.lesson_id,
            "tutor_id": row.tutor_id,
            "rating": row.rating,
            "comment": row.comment
        })
    return feedbacks


async def get_tutor_by_user_id(db: AsyncSession, user_id: int):
    query = text("""
        SELECT tutor_id, user_id, description, experience, rating
        FROM tutors
        WHERE user_id = :user_id
        LIMIT 1;
    """)
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()
    if row:
        return {
            "tutor_id": row.tutor_id,
            "user_id": row.user_id,
            "description": row.description,
            "experience": row.experience,
            "rating": float(row.rating)
        }
    return None

async def get_student_by_user_id(db: AsyncSession, user_id: int):
    query = text("""
        SELECT student_id, user_id, education_level, interests
        FROM students
        WHERE user_id = :user_id
        LIMIT 1;
    """)
    result = await db.execute(query, {"user_id": user_id})
    row = result.fetchone()
    if row:
        return {
            "student_id": row.student_id,
            "user_id": row.user_id,
            "education_level": row.education_level,
            "interests": row.interests
        }
    return None
