-- Create Database
CREATE DATABASE IF NOT EXISTS preqaboard;

-- Select Database
USE preqaboard;


    -- ===========================================================
-- TABLE 1 : DEPARTMENT
-- Admin creates departments.
-- Example:
-- Computer Applications
-- Computer Science
-- Management
-- ===========================================================

CREATE TABLE department(
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 2 : COURSE
-- Admin creates courses under departments.
-- Example:
-- Computer Applications
--      ├── MCA
--      └── BCA
-- ===========================================================

CREATE TABLE course(
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    duration_years INT NOT NULL,
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(department_id)
    REFERENCES department(department_id)
    ON DELETE CASCADE,
    UNIQUE(department_id,course_name)

);


-- ===========================================================
-- TABLE 3 : SEMESTER
-- HOD creates semesters for courses
-- Supports 2,4,6,8 or any number of semesters
-- ===========================================================

CREATE TABLE semester(
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_number INT NOT NULL,
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id)
    REFERENCES course(course_id)
    ON DELETE CASCADE,
    UNIQUE(course_id,semester_number)
);


-- ===========================================================
-- TABLE 4 : ADMIN
-- System Administrator
-- Only one or more administrators manage the system.
-- ===========================================================

CREATE TABLE admin(
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP

);

-- DEFAULT ADMIN ACCOUNT
-- Used for first login

    INSERT INTO admin
(
    username,
    password,
    full_name,
    email,
    phone,
    status
)
VALUES
(
    'admin',
    'admin123',
    'System Administrator',
    'admin@preqaboard.com',
    '9999999999',
    'Active'
);



-- ===========================================================
-- TABLE 6 : TEACHER
-- HOD creates Teacher accounts.
-- Teachers may teach multiple subjects and courses.
-- ===========================================================

CREATE TABLE teacher(
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    username VARCHAR(50) UNIQUE,
    password VARCHAR(255),
    account_status ENUM('Pending','Active','Inactive')
    DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP

);


-- ===========================================================
-- TABLE 7 : STUDENT
-- Students register themselves.
-- ===========================================================

CREATE TABLE student(
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_id INT NOT NULL,
    register_number VARCHAR(30) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    account_status ENUM('Pending','Active','Inactive')
    DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id)
    REFERENCES course(course_id)
    ON DELETE CASCADE,
    FOREIGN KEY(semester_id)
    REFERENCES semester(semester_id)
    ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 8 : ACADEMIC YEAR
-- Admin manages academic years.
-- Example:
-- 2025-2026
-- 2026-2027
-- ===========================================================

CREATE TABLE academic_year(
    academic_year_id INT AUTO_INCREMENT PRIMARY KEY,
    academic_year_name VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status ENUM('Current','Completed','Upcoming')
    DEFAULT 'Upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 9 : SUBJECT
-- HOD adds subjects for each course and semester.
-- ===========================================================

CREATE TABLE subject(
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_id INT NOT NULL,
    subject_code VARCHAR(20) NOT NULL UNIQUE,
    subject_name VARCHAR(150) NOT NULL,
    credits INT DEFAULT 4,
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY(course_id)
    REFERENCES course(course_id)
    ON DELETE CASCADE,
    FOREIGN KEY(semester_id)
    REFERENCES semester(semester_id)
    ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 10 : TEACHER SUBJECT ASSIGNMENT
-- HOD assigns teachers to subjects.
-- ===========================================================

CREATE TABLE teacher_subject_assignment(
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    assigned_by_hod INT NOT NULL,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    FOREIGN KEY(teacher_id)
    REFERENCES teacher(teacher_id)
    ON DELETE CASCADE,
    FOREIGN KEY(subject_id)
    REFERENCES subject(subject_id)
    ON DELETE CASCADE,
    FOREIGN KEY(academic_year_id)
    REFERENCES academic_year(academic_year_id)
    ON DELETE CASCADE,
    FOREIGN KEY(assigned_by_hod)
    REFERENCES hod(hod_id)
    ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 11 : EXAM TYPE
-- Admin manages exam types.
-- ===========================================================

CREATE TABLE exam_type(
    exam_type_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_type_name VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('Active','Inactive')
    DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 12 : QUESTION PAPER
-- Teachers upload question papers.
-- ===========================================================

CREATE TABLE question_paper(
    question_paper_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    exam_type_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    academic_year_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    uploaded_by INT NOT NULL,
    approved_by_hod BOOLEAN DEFAULT FALSE,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assignment_id)
    REFERENCES teacher_subject_assignment(assignment_id),
    FOREIGN KEY(exam_type_id)
    REFERENCES exam_type(exam_type_id),
    FOREIGN KEY(academic_year_id)
    REFERENCES academic_year(academic_year_id),
    FOREIGN KEY(uploaded_by)
    REFERENCES teacher(teacher_id)
);


-- ===========================================================
-- TABLE 13 : STUDY MATERIAL
-- ===========================================================

CREATE TABLE study_material(
    study_material_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    title VARCHAR(200),
    file_name VARCHAR(255),
    uploaded_by INT NOT NULL,
    approved_by_hod BOOLEAN DEFAULT FALSE,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(assignment_id)
    REFERENCES teacher_subject_assignment(assignment_id),
    FOREIGN KEY(uploaded_by)
    REFERENCES teacher(teacher_id)

);


-- ===========================================================
-- TABLE 14 : ANSWER KEY
-- ===========================================================

CREATE TABLE answer_key(
    answer_key_id INT AUTO_INCREMENT PRIMARY KEY,
    question_paper_id INT NOT NULL,
    file_name VARCHAR(255),
    uploaded_by INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(question_paper_id)
    REFERENCES question_paper(question_paper_id)
    ON DELETE CASCADE,
    FOREIGN KEY(uploaded_by)
    REFERENCES teacher(teacher_id)
);


-- ===========================================================
-- TABLE 15 : EXTRACTED QUESTION
-- AI Extracted Questions
-- ===========================================================

CREATE TABLE extracted_question(
    extracted_question_id INT AUTO_INCREMENT PRIMARY KEY,
    question_paper_id INT NOT NULL,
    question_number VARCHAR(20),
    question_text TEXT,
    marks INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(question_paper_id)
    REFERENCES question_paper(question_paper_id)
    ON DELETE CASCADE

);


-- ===========================================================
-- TABLE 16 : REPEATED QUESTION
-- ===========================================================

CREATE TABLE repeated_question(
    repeated_question_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    question_text TEXT,
    repeated_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(subject_id)
    REFERENCES subject(subject_id)
    ON DELETE CASCADE

);


-- ===========================================================
-- TABLE 17 : STUDENT DOUBT
-- ===========================================================

CREATE TABLE student_doubt(
    doubt_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    doubt_title VARCHAR(255),
    doubt_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id)
    REFERENCES student(student_id),
    FOREIGN KEY(subject_id)
    REFERENCES subject(subject_id)
);


-- ===========================================================
-- TABLE 18 : TEACHER REPLY
-- ===========================================================

CREATE TABLE teacher_reply(
    reply_id INT AUTO_INCREMENT PRIMARY KEY,
    doubt_id INT NOT NULL,
    teacher_id INT NOT NULL,
    reply TEXT,
    replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(doubt_id)
    REFERENCES student_doubt(doubt_id)
    ON DELETE CASCADE,
    FOREIGN KEY(teacher_id)
    REFERENCES teacher(teacher_id)
);