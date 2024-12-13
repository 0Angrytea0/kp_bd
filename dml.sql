--dml
-- Вставка ролей
INSERT INTO roles (role_name) VALUES 
('Administrator'), 
('Tutor'), 
('Student');

-- Вставка администратора
INSERT INTO users (first_name, last_name, email, phone, role_id) VALUES
('Admin', 'User', 'admin@example.com', '1234567890', 1);

-- Хешированный пароль для администратора
INSERT INTO authentication (user_id, password_hash, salt) VALUES
(1, '$2b$12$hS6s6BGJOLYpTuVGaeQP1OjfRI9F5LNGVNy0x5zT2meaGYQz01toC', 'not_used_with_bcrypt');

-- Вставка предметов
INSERT INTO subjects (subject_name, description) VALUES
('Mathematics', 'Advanced mathematical concepts and techniques'),
('Physics', 'Basic and advanced physics topics'),
('Chemistry', 'Introductory and advanced chemistry lessons');
