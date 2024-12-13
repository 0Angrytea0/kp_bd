# app/main.py

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from contextlib import asynccontextmanager
from sqlalchemy import text
from .database import get_db
from .utils import create_access_token, verify_password
from .auth import get_current_user
from . import crud, schemas

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user["auth"]["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user["user_id"])})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=schemas.UserOut)
async def create_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Проверяем существование пользователя
    existing_user_email = await crud.get_user_by_email(db, user.email)
    existing_user_phone = await crud.get_user_by_phone(db, user.phone)
    if existing_user_email or existing_user_phone:
        raise HTTPException(status_code=400, detail="User with this email or phone already exists")

    # Создаём пользователя
    new_user = await crud.create_user(db, user)

    # Создаём запись в таблице tutors или students
    if user.role_id == 2:  # Если репетитор
        tutor_data = schemas.TutorCreate(
            user_id=new_user["user_id"],
            description="Описание не указано",
            experience=0
        )
        await crud.create_tutor(db, tutor_data)
    elif user.role_id == 3:  # Если ученик
        student_data = schemas.StudentCreate(
            user_id=new_user["user_id"],
            education_level="Beginner",
            interests=""
        )
        await crud.create_student(db, student_data)

    # Получаем данные для ответа
    tutor = await crud.get_tutor_by_user_id(db, new_user["user_id"])
    student = await crud.get_student_by_user_id(db, new_user["user_id"])

    return {
        "user_id": new_user["user_id"],
        "first_name": new_user["first_name"],
        "last_name": new_user["last_name"],
        "email": new_user["email"],
        "phone": new_user["phone"],
        "role_id": new_user["role_id"],
        "tutor_id": tutor["tutor_id"] if tutor else None,
        "student_id": student["student_id"] if student else None
    }


@app.get("/users/me/", response_model=schemas.UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Получаем данные о репетиторе и ученике
    tutor = await crud.get_tutor_by_user_id(db, current_user["user_id"])
    student = await crud.get_student_by_user_id(db, current_user["user_id"])

    return {
        "user_id": current_user["user_id"],
        "first_name": current_user["first_name"],
        "last_name": current_user["last_name"],
        "email": current_user["email"],
        "phone": current_user["phone"],
        "role_id": current_user["role_id"],
        "tutor_id": tutor["tutor_id"] if tutor else None,
        "student_id": student["student_id"] if student else None
    }


@app.post("/tutors/")
async def create_tutor_endpoint(tutor: schemas.TutorCreate, db: AsyncSession = Depends(get_db)):
    new_tutor = await crud.create_tutor(db, tutor)
    return new_tutor

@app.get("/tutors/", response_model=List[schemas.TutorOut])
async def get_tutors_endpoint(db: AsyncSession = Depends(get_db)):
    tutors = await crud.get_tutors(db)
    tutor_out_list = []
    for t in tutors:
        user_data = await crud.get_user(db, t["user_id"])
        tutor_out_list.append({
            "tutor_id": t["tutor_id"],
            "user": {
                "user_id": user_data["user_id"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "email": user_data["email"],
                "phone": user_data["phone"],
                "role_id": user_data["role_id"],
                "tutor_id": None,
                "student_id": None,
            },
            "description": t["description"],
            "experience": t["experience"],
            "rating": t["rating"]
        })
    return tutor_out_list

@app.get("/tutors/{tutor_id}", response_model=schemas.TutorOut)
async def read_tutor(tutor_id: int, db: AsyncSession = Depends(get_db)):
    t = await crud.get_tutor(db, tutor_id)
    if not t:
        raise HTTPException(status_code=404, detail="Репетитор не найден")
    user_data = await crud.get_user(db, t["user_id"])
    return {
        "tutor_id": t["tutor_id"],
        "user": {
            "user_id": user_data["user_id"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "role_id": user_data["role_id"],
            "tutor_id": None,
            "student_id": None
        },
        "description": t["description"],
        "experience": t["experience"],
        "rating": t["rating"]
    }

@app.put("/tutors/{tutor_id}/description")
async def update_tutor_description(
    tutor_id: int,
    update_data: schemas.UpdateTutorInfoRequest,
    db: AsyncSession = Depends(get_db),
):
    query = text("""
        UPDATE tutors
        SET description = COALESCE(:description, description),
            experience = COALESCE(:experience, experience)
        WHERE tutor_id = :tutor_id
        RETURNING tutor_id, description, experience;
    """)
    result = await db.execute(
        query,
        {
            "description": update_data.description,
            "experience": update_data.experience,
            "tutor_id": tutor_id,
        },
    )
    updated_row = result.fetchone()
    await db.commit()

    if not updated_row:
        raise HTTPException(status_code=404, detail="Репетитор не найден")

    return {
        "tutor_id": updated_row.tutor_id,
        "description": updated_row.description,
        "experience": updated_row.experience,
    }

@app.post("/students/")
async def create_student_endpoint(student: schemas.StudentCreate, db: AsyncSession = Depends(get_db)):
    new_student = await crud.create_student(db, student)
    return new_student

@app.get("/students/{student_id}", response_model=schemas.StudentOut)
async def read_student(student_id: int, db: AsyncSession = Depends(get_db)):
    s = await crud.get_student(db, student_id)
    if s is None:
        raise HTTPException(status_code=404, detail="Ученик не найден")
    user_data = await crud.get_user(db, s["user_id"])
    return {
        "student_id": s["student_id"],
        "user": {
            "user_id": user_data["user_id"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "role_id": user_data["role_id"],
            "tutor_id": None,
            "student_id": None
        },
        "education_level": s["education_level"],
        "interests": s["interests"]
    }

@app.put("/students/{student_id}")
async def update_student_profile(
    student_id: int,
    update_data: schemas.StudentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Проверяем, что текущий пользователь — это студент
    if current_user["role_id"] != 3:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    query = text("""
        UPDATE students
        SET education_level = :education_level
        WHERE student_id = :student_id
        RETURNING student_id, education_level, interests;
    """)
    result = await db.execute(query, {
        "education_level": update_data.education_level,
        "student_id": student_id
    })
    updated_row = result.fetchone()
    await db.commit()

    if not updated_row:
        raise HTTPException(status_code=404, detail="Ученик не найден")

    return {
        "student_id": updated_row.student_id,
        "education_level": updated_row.education_level,
        "interests": updated_row.interests,
    }


@app.post("/lessons/", response_model=schemas.LessonOut)
async def create_lesson_endpoint(lesson: schemas.LessonCreate, db: AsyncSession = Depends(get_db)):
    new_lesson = await crud.create_lesson(db, lesson)
    if not new_lesson:
        raise HTTPException(status_code=500, detail="Не удалось создать урок")
    return new_lesson

@app.get("/lessons/student/{student_id}", response_model=List[schemas.LessonOut])
async def get_lessons_by_student_endpoint(student_id: int, db: AsyncSession = Depends(get_db)):
    lessons = await crud.get_lessons_by_student(db, student_id)
    return lessons



@app.get("/lessons/tutor/{tutor_id}", response_model=List[schemas.LessonOut])
async def get_lessons_by_tutor_endpoint(tutor_id: int, db: AsyncSession = Depends(get_db)):
    # Получаем данные о занятиях напрямую через CRUD
    lessons = await crud.get_lessons_by_tutor(db, tutor_id)

    return lessons


@app.put("/lessons/{lesson_id}/status")
async def update_lesson_status(
    lesson_id: int,
    request: schemas.UpdateLessonStatusRequest,  # Используем вашу новую схему
    db: AsyncSession = Depends(get_db),
):
    valid_statuses = ["scheduled", "completed", "canceled"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Некорректный статус")

    query = text("""
        UPDATE lessons
        SET status = :status
        WHERE lesson_id = :lesson_id
        RETURNING lesson_id;
    """)
    result = await db.execute(query, {"status": request.status, "lesson_id": lesson_id})
    updated_row = result.fetchone()
    await db.commit()

    if not updated_row:
        raise HTTPException(status_code=404, detail="Занятие не найдено")
    return {"message": "Статус обновлен"}


@app.get("/feedbacks/tutor/{tutor_id}", response_model=List[schemas.FeedbackOut])
async def read_feedbacks_by_tutor(tutor_id: int, db: AsyncSession = Depends(get_db)):
    feedbacks = await crud.get_feedbacks_by_tutor(db, tutor_id)
    return feedbacks

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
