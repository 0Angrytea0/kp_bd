from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, time


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    role_id: int


class UserOut(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    role_id: int
    tutor_id: Optional[int] = None
    student_id: Optional[int] = None

    class Config:
        orm_mode = False  


class Token(BaseModel):
    access_token: str
    token_type: str


class TutorCreate(BaseModel):
    user_id: int
    description: str
    experience: int = 0


class TutorOut(BaseModel):
    tutor_id: int
    user: UserOut
    description: Optional[str] = None
    experience: int
    rating: float

    class Config:
        orm_mode = False  


class StudentCreate(BaseModel):
    user_id: int
    education_level: str
    interests: str


class StudentOut(BaseModel):
    student_id: int
    user: UserOut
    education_level: str
    interests: Optional[str] = None

    class Config:
        orm_mode = False  


class StudentUpdate(BaseModel):
    education_level: str


class LessonCreate(BaseModel):
    tutor_id: int
    student_id: int
    subject_id: int
    lesson_date: date
    lesson_time: time
    status: Optional[str] = "scheduled"


class LessonOut(BaseModel):
    lesson_id: int
    tutor_id: int
    student_id: int
    subject_id: int
    lesson_date: date
    lesson_time: time
    status: str

    class Config:
        orm_mode = False  


class FeedbackCreate(BaseModel):
    lesson_id: int
    tutor_id: int
    student_id: int
    rating: int
    comment: Optional[str] = None


class FeedbackOut(BaseModel):
    feedback_id: int
    lesson_id: int
    tutor_id: int
    rating: int
    comment: Optional[str] = None

    class Config:
        orm_mode = False  

class SubjectOut(BaseModel):
    subject_id: int
    subject_name: str
    description: Optional[str] = None

    class Config:
        orm_mode = False



class UpdateTutorInfoRequest(BaseModel):
    description: Optional[str] = None
    experience: Optional[int] = None

class UpdateLessonStatusRequest(BaseModel):
    status: str
