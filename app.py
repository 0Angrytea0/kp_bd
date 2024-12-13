# app.py

import streamlit as st
import requests
import asyncio
import httpx

API_URL = "http://localhost:8000"

def login():
    st.title("Вход")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        response = requests.post(f"{API_URL}/token", data={"username": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state['access_token'] = data['access_token']
            st.success("Успешный вход")
            st.rerun()
        else:
            st.error("Неверный email или пароль")

def register():
    st.title("Регистрация")
    first_name = st.text_input("Имя")
    last_name = st.text_input("Фамилия")
    email = st.text_input("Email")
    phone = st.text_input("Телефон")
    password = st.text_input("Пароль", type="password")
    role = st.selectbox("Роль", ["Student", "Tutor"])

    if st.button("Зарегистрироваться"):
        role_id = 2 if role == "Tutor" else 3  # 2 - Tutor, 3 - Student
        user_data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "password": password,
            "role_id": role_id
        }

        # Регистрация пользователя в таблице users
        response = requests.post(f"{API_URL}/users/", json=user_data)

        if response.status_code == 200:
            st.success("Успешная регистрация! Теперь вы можете войти.")
        else:
            st.error("Ошибка регистрации пользователя.")

def get_tutors(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/tutors/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error("Failed to fetch tutors")
        return []
    
def show_tutors():
    st.title("Список репетиторов")

    # Получение токена из сессии
    token = st.session_state.get("access_token")
    if not token:
        st.error("Вы не авторизованы!")
        return

    # Получение списка репетиторов
    tutors = get_tutors(token)

    if not tutors:
        st.info("Список репетиторов пуст.")
        return

    # Отображение репетиторов
    for tutor in tutors:
        st.subheader(f"{tutor['user']['first_name']} {tutor['user']['last_name']}")
        st.write(f"Описание: {tutor['description']}")
        st.write(f"Опыт: {tutor['experience']} лет")
        st.write(f"Рейтинг: {tutor['rating']} ⭐")
        st.write("---")


def main():
    if 'access_token' not in st.session_state:
        page = st.sidebar.selectbox("Выберите действие", ["Вход", "Регистрация"])
        if page == "Вход":
            login()
        elif page == "Регистрация":
            register()
    else:
        token = st.session_state['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/users/me/", headers=headers)
        if response.status_code == 200:
            user = response.json()
            st.title(f"Добро пожаловать, {user['first_name']}!")
            role_id = user['role_id']
            if role_id == 1:
                st.subheader("Панель администратора")
                admin_panel(headers)
            elif role_id == 2:
                # Это преподаватель
                st.session_state["tutor_id"] = user.get("tutor_id")
                tutor_panel(headers, user)
            elif role_id == 3:
                # Это студент
                st.session_state["student_id"] = user.get("student_id")
                student_panel(headers, user)
            else:
                st.error("Неизвестная роль пользователя")
        else:
            st.error("Не удалось получить данные пользователя")
            del st.session_state['access_token']
            st.rerun()

def admin_panel(headers):
    st.subheader("Функции администратора")
    st.write("Функции пока не реализованы.")

def tutor_panel(headers, user):
    # Получение tutor_id из сессии
    tutor_id = st.session_state.get("tutor_id")
    if not tutor_id:
        st.error("Ошибка: Не удалось определить ID репетитора.")
        return

    # Боковое меню
    action = st.sidebar.radio("Действия", ["Моё расписание", "Добавить занятие", "Редактировать описание"])

    # Отображение расписания
    if action == "Моё расписание":
        st.subheader("Расписание")
        token = headers["Authorization"].split(" ")[1]
        schedule = fetch_schedule(tutor_id, token)
        display_schedule(schedule, token)

    # Добавление занятия
    elif action == "Добавить занятие":
        st.subheader("Добавить новое занятие")

        student_id = st.text_input("ID ученика")
        subject_id = st.text_input("ID предмета")
        lesson_date = st.date_input("Дата занятия")
        lesson_time = st.time_input("Время занятия")

        if st.button("Добавить"):
            lesson_data = {
                "tutor_id": tutor_id,
                "student_id": int(student_id),
                "subject_id": int(subject_id),
                "lesson_date": str(lesson_date),
                "lesson_time": str(lesson_time),
                "status": "scheduled",
            }
            response = requests.post(f"{API_URL}/lessons/", headers=headers, json=lesson_data)
            if response.status_code == 200:
                st.success("Занятие успешно добавлено!")
            else:
                st.error("Ошибка при добавлении занятия.")
        
    elif action == "Редактировать описание":
        st.subheader("Изменить описание и опыт работы")


        # Получить текущие данные
        response = requests.get(f"{API_URL}/tutors/{tutor_id}", headers=headers)
        if response.status_code == 200:
            tutor_info = response.json()
            current_description = tutor_info["description"]
            current_experience = tutor_info["experience"]
        else:
            st.error("Не удалось загрузить информацию о репетиторе.")
            return

        # Поля для изменения
        new_description = st.text_area("Описание", value=current_description)
        new_experience = st.number_input("Опыт работы (в годах)", value=current_experience, step=1, min_value=0)

        if st.button("Сохранить изменения"):
            token = headers["Authorization"].split(" ")[1]
            update_tutor_description(tutor_id, new_description, new_experience, token)


def update_tutor_description(tutor_id, description, experience, token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"description": description, "experience": experience}
    response = requests.put(f"{API_URL}/tutors/{tutor_id}/description", json=data, headers=headers)
    if response.status_code == 200:
        st.success("Информация успешно обновлена!")
    else:
        st.error(f"Ошибка при обновлении данных: {response.json()}")

def fetch_schedule(tutor_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/lessons/tutor/{tutor_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Ошибка при загрузке расписания: {response.status_code}")
        return []

def update_lesson_status(lesson_id, new_status, token):
    headers = {"Authorization": f"Bearer {token}"}
    data = {"status": new_status}  # Обратите внимание, формат должен соответствовать схеме
    response = requests.put(f"{API_URL}/lessons/{lesson_id}/status", json=data, headers=headers)
    if response.status_code == 200:
        st.success("Статус успешно обновлен!")
    else:
        st.error(f"Ошибка при обновлении статуса: {response.status_code}")



def display_schedule(schedule, token):
    if not schedule:
        st.info("Расписание пока пусто.")
        return

    # Словарь названий предметов
    subject_names = {
        1: "Mathematics",
        2: "Physics",
        3: "Chemistry"
    }

    for lesson in schedule:
        student_details = fetch_student_details(lesson['student_id'], token)
        if student_details:
            student_name = f"{student_details['user']['first_name']} {student_details['user']['last_name']}"
            education_level =  student_details.get("education_level")
        else:
            student_name = "Неизвестный ученик"
            education_level = "Неизвестно"

        # Получаем subject_id и находим название предмета через словарь
        subject_id = lesson['subject_id']
        subject_name = subject_names.get(subject_id, "Неизвестный предмет")

        st.write(f"Дата: {lesson['lesson_date']}, Время: {lesson['lesson_time']}")
        st.write(f"Ученик: {student_name} (Уровень образования: {education_level})")
        st.write(f"Предмет: {subject_name}")
        st.write(f"Статус: {lesson['status']}")

        new_status = st.selectbox(
            "Изменить статус занятия",
            options=["scheduled", "completed", "canceled"],
            index=["scheduled", "completed", "canceled"].index(lesson['status']),
            key=f"status_{lesson['lesson_id']}"
        )

        if st.button("Обновить статус", key=f"update_status_{lesson['lesson_id']}"):
            update_lesson_status(lesson['lesson_id'], new_status, token)

        st.write("---")

def fetch_student_details(student_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/students/{student_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


def student_panel(headers, user):

    # Получаем student_id из сессии
    student_id = st.session_state.get("student_id")
    if not student_id:
        st.error("Ошибка: не удалось определить ID ученика.")
        return

    action = st.sidebar.radio("Действия", ["Мой профиль", "Моё расписание", "Поиск репетиторов"])

    # Действие: Поиск репетиторов
    if action == "Поиск репетиторов":
        st.subheader("Поиск репетиторов")
        st.info(f"Ваш ID: {student_id}")
        response = requests.get(f"{API_URL}/tutors/", headers=headers)
        if response.status_code == 200:
            tutors = response.json()
            for tutor in tutors:
                # Информация о репетиторе
                st.write(f"Репетитор: {tutor['user']['first_name']} {tutor['user']['last_name']} (Рейтинг: {tutor['rating']})")
                st.write(f"Описание: {tutor['description']}")
                st.write(f"Email: {tutor['user']['email']}")
                st.write(f"Опыт: {tutor['experience']} лет")

                # Кнопка для просмотра отзывов
                
                view_feedbacks(tutor['tutor_id'], headers["Authorization"].split(" ")[1])

                # Форма для оставления отзыва
                submit_feedback(tutor['tutor_id'], headers["Authorization"].split(" ")[1], student_id)

                st.write("---")
        else:
            st.error("Не удалось загрузить список репетиторов")

    # Действие: Моё расписание
    elif action == "Моё расписание":
        st.subheader("Расписание")
        token = headers["Authorization"].split(" ")[1]
        schedule = fetch_student_schedule(student_id, token)
        display_student_schedule(schedule)

    elif action == "Мой профиль":
        st.subheader("Ваш профиль")
        token = headers["Authorization"].split(" ")[1]
        response = requests.get(f"{API_URL}/students/{student_id}", headers=headers)

        if response.status_code == 200:
            student_data = response.json()
            st.write(f"Имя: {user['first_name']} {user['last_name']}")
            st.write(f"Email: {user['email']}")
            st.write(f"Телефон: {user['phone']}")

            # Добавить текущий уровень образования
            current_level = student_data['education_level']
            new_level = st.selectbox(
                "Уровень образования",
                ["Beginner", "Elementary", "Intermediate"],
                index=["Beginner", "Elementary", "Intermediate"].index(current_level)
            )

            if st.button("Обновить профиль"):
                update_data = {"education_level": new_level}
                update_response = requests.put(
                    f"{API_URL}/students/{student_id}",
                    headers=headers,
                    json=update_data
                )
                if update_response.status_code == 200:
                    st.success("Уровень образования успешно обновлен!")
                else:
                    st.error("Ошибка при обновлении данных.")
        else:
            st.error("Не удалось загрузить данные профиля.")


def fetch_student_schedule(student_id, token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/lessons/student/{student_id}", headers=headers)
    if response.status_code == 200:
        schedule = response.json()
        return schedule
    else:
        st.error(f"Ошибка при загрузке расписания: {response.status_code}")
        return []

def display_student_schedule(schedule):
    if not schedule:
        st.info("Расписание пока пусто.")
        return

    # Словарь для предметов по subject_id
    subject_names = {
        1: "Mathematics",
        2: "Physics",
        3: "Chemistry"
    }

    # Получаем токен из сессии
    token = st.session_state.get("access_token")
    if not token:
        st.error("Отсутствует токен аутентификации.")
        return
    headers = {"Authorization": f"Bearer {token}"}

    for lesson in schedule:
        tutor_id = lesson["tutor_id"]
        subject_id = lesson["subject_id"]
        
        # Получаем имя предмета из словаря
        subject_name = subject_names.get(subject_id, "Неизвестный предмет")

        # Делаем запрос к /tutors/{tutor_id}, чтобы получить данные о преподавателе
        tutor_response = requests.get(f"{API_URL}/tutors/{tutor_id}", headers=headers)
        if tutor_response.status_code == 200:
            tutor_data = tutor_response.json()
            tutor_name = f"{tutor_data['user']['first_name']} {tutor_data['user']['last_name']}"
        else:
            tutor_name = "Неизвестный преподаватель"

        # Извлекаем данные о занятии
        date = lesson["lesson_date"]
        time = lesson["lesson_time"]
        status = lesson["status"]

        # Выводим информацию
        st.write(f"Дата: {date}, Время: {time}")
        st.write(f"Преподаватель: {tutor_name}")
        st.write(f"Предмет: {subject_name}")
        st.write(f"Статус: {status}")
        st.write("---")





def submit_feedback(tutor_id, token, student_id):
    st.subheader(f"Оставить отзыв для преподавателя")

    # Инициализация состояния для отображения формы
    if f"show_feedback_form_{tutor_id}" not in st.session_state:
        st.session_state[f"show_feedback_form_{tutor_id}"] = False

    # Кнопка для открытия/закрытия формы
    if st.button("Оставить отзыв", key=f"toggle_feedback_form_{tutor_id}"):
        st.session_state[f"show_feedback_form_{tutor_id}"] = not st.session_state[f"show_feedback_form_{tutor_id}"]

    # Если форма не должна быть показана, ничего не делаем
    if not st.session_state[f"show_feedback_form_{tutor_id}"]:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Получение списка уроков между студентом и преподавателем
    lessons_url = f"{API_URL}/lessons/student/{student_id}"
    lessons_response = requests.get(lessons_url, headers=headers)

    if lessons_response.status_code == 200:
        lessons = lessons_response.json()
        tutor_lessons = [
            lesson for lesson in lessons if lesson["tutor"]["tutor_id"] == tutor_id
        ]

        if not tutor_lessons:
            st.warning("Нет уроков с этим преподавателем, отзыв недоступен.")
            return
    else:
        st.error("Ошибка при получении уроков. Попробуйте позже.")
        return

    # Выбор урока
    lesson_choices = {
        f"{lesson['lesson_date']} {lesson['lesson_time']} - {lesson['subject']['subject_name']}":
        lesson["lesson_id"]
        for lesson in tutor_lessons
    }

    with st.form(key=f"feedback_form_{tutor_id}"):
        # Cписок уроков
        selected_lesson = st.selectbox(
            "Выберите урок для отзыва", options=list(lesson_choices.keys())
        )
        lesson_id = lesson_choices[selected_lesson]

        rating = st.slider("Рейтинг", min_value=1, max_value=5, key=f"rating_{tutor_id}")
        comment = st.text_area("Комментарий (опционально)", key=f"comment_{tutor_id}")
        submitted = st.form_submit_button("Отправить отзыв")

        if submitted:
            feedback_data = {
                "lesson_id": lesson_id,  
                "tutor_id": tutor_id,
                "student_id": student_id,
                "rating": rating,
                "comment": comment,
            }
            response = requests.post(f"{API_URL}/feedbacks/", headers=headers, json=feedback_data)
            if response.status_code == 200:
                st.success("Отзыв успешно добавлен!")
                # Скрываем форму после отправки
                st.session_state[f"show_feedback_form_{tutor_id}"] = False
            else:
                st.error(f"Ошибка при добавлении отзыва: {response.text}")


def view_feedbacks(tutor_id, token):
    # Инициализация состояния для отображения отзывов
    if f"show_reviews_{tutor_id}" not in st.session_state:
        st.session_state[f"show_reviews_{tutor_id}"] = False

    # Кнопка для открытия/закрытия раздела с отзывами
    if st.button("Посмотреть отзывы", key=f"toggle_reviews_{tutor_id}"):
        st.session_state[f"show_reviews_{tutor_id}"] = not st.session_state[f"show_reviews_{tutor_id}"]

    # Если включено состояние отображения отзывов, загружаем их
    if st.session_state[f"show_reviews_{tutor_id}"]:
        st.subheader(f"Отзывы о преподавателе")

        # Запрос отзывов для преподавателя
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/feedbacks/tutor/{tutor_id}", headers=headers)

        if response.status_code == 200:
            feedbacks = response.json()
            if feedbacks:
                for feedback in feedbacks:
                    st.write(f"Рейтинг: {feedback['rating']} ⭐")
                    st.write(f"Комментарий: {feedback['comment']}")
                    st.write("---")
            else:
                st.info("У этого преподавателя пока нет отзывов.")
        else:
            st.error("Ошибка при загрузке отзывов.")




if __name__ == "__main__":
    main()
