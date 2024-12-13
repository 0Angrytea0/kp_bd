--ddl
-- Создание таблицы ролей
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

-- Создание таблицы пользователей
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    role_id INTEGER REFERENCES roles(role_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы аутентификации
CREATE TABLE authentication (
    auth_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL
);

-- Создание таблицы репетиторов
CREATE TABLE tutors (
    tutor_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    description TEXT,
    experience INTEGER NOT NULL DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0.00
);

-- Создание таблицы учеников
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    education_level VARCHAR(50),
    interests TEXT
);

-- Создание таблицы предметов
CREATE TABLE subjects (
    subject_id SERIAL PRIMARY KEY,
    subject_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- Создание таблицы занятий
CREATE TABLE lessons (
    lesson_id SERIAL PRIMARY KEY,
    tutor_id INTEGER REFERENCES tutors(tutor_id) ON DELETE CASCADE,
    student_id INTEGER REFERENCES students(student_id) ON DELETE CASCADE,
    subject_id INTEGER REFERENCES subjects(subject_id) ON DELETE CASCADE,
    lesson_date DATE NOT NULL,
    lesson_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled'
);

-- Создание таблицы отзывов
CREATE TABLE feedbacks (
    feedback_id SERIAL PRIMARY KEY,
    lesson_id INTEGER REFERENCES lessons(lesson_id) ON DELETE CASCADE,
    tutor_id INTEGER REFERENCES tutors(tutor_id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comment TEXT
);

CREATE OR REPLACE FUNCTION update_tutor_rating_func()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tutors
    SET rating = (
        SELECT COALESCE(AVG(rating)::DECIMAL(3,2), 0.00)
        FROM feedbacks
        WHERE tutor_id = NEW.tutor_id
    )
    WHERE tutor_id = NEW.tutor_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_tutor_rating
AFTER INSERT OR DELETE OR UPDATE OF rating
ON feedbacks
FOR EACH ROW
EXECUTE PROCEDURE update_tutor_rating_func();