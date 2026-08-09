-- ===========================================================
-- PREQABOARD DATABASE
-- COMPLETE DATABASE SQL - SAFE VERSION
-- ===========================================================

CREATE DATABASE IF NOT EXISTS preqaboard;

USE preqaboard;


-- ===========================================================
-- TABLE 1 : DEPARTMENT
-- ===========================================================

CREATE TABLE IF NOT EXISTS department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 2 : COURSE
-- ===========================================================

CREATE TABLE IF NOT EXISTS course (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    duration_years INT NOT NULL,
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (department_id)
        REFERENCES department(department_id)
        ON DELETE CASCADE,

    UNIQUE (department_id, course_name)
);


-- ===========================================================
-- TABLE 3 : SEMESTER
-- ===========================================================

CREATE TABLE IF NOT EXISTS semester (
    semester_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_number INT NOT NULL,
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id)
        REFERENCES course(course_id)
        ON DELETE CASCADE,

    UNIQUE (course_id, semester_number)
);


-- ===========================================================
-- TABLE 4 : ADMIN
-- ===========================================================

CREATE TABLE IF NOT EXISTS admin (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(15),
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ===========================================================
-- DEFAULT ADMIN ACCOUNT
-- ===========================================================

INSERT IGNORE INTO admin (
    username,
    password,
    full_name,
    email,
    phone,
    status
)
VALUES (
    'admin',
    'admin123',
    'System Administrator',
    'admin@preqaboard.com',
    '9999999999',
    'Active'
);


-- ===========================================================
-- TABLE 5 : HOD
-- ===========================================================

CREATE TABLE IF NOT EXISTS hod (
    hod_id INT AUTO_INCREMENT PRIMARY KEY,
    department_id INT NOT NULL,
    employee_id VARCHAR(20) NOT NULL UNIQUE,
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

    FOREIGN KEY (department_id)
        REFERENCES department(department_id)
        ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 6 : TEACHER
-- ===========================================================

CREATE TABLE IF NOT EXISTS teacher (
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
-- ===========================================================

CREATE TABLE IF NOT EXISTS student (
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

    FOREIGN KEY (course_id)
        REFERENCES course(course_id)
        ON DELETE CASCADE,

    FOREIGN KEY (semester_id)
        REFERENCES semester(semester_id)
        ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 8 : ACADEMIC YEAR
-- ===========================================================

CREATE TABLE IF NOT EXISTS academic_year (
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
-- ===========================================================

CREATE TABLE IF NOT EXISTS subject (
    subject_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    semester_id INT NOT NULL,
    subject_code VARCHAR(20) NOT NULL UNIQUE,
    subject_name VARCHAR(150) NOT NULL,
    credits INT DEFAULT 4,
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (course_id)
        REFERENCES course(course_id)
        ON DELETE CASCADE,

    FOREIGN KEY (semester_id)
        REFERENCES semester(semester_id)
        ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 10 : TEACHER SUBJECT ASSIGNMENT
-- ===========================================================

CREATE TABLE IF NOT EXISTS teacher_subject_assignment (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    teacher_id INT NOT NULL,
    subject_id INT NOT NULL,
    academic_year_id INT NOT NULL,
    assigned_by_hod INT NOT NULL,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Active','Inactive') DEFAULT 'Active',

    FOREIGN KEY (teacher_id)
        REFERENCES teacher(teacher_id)
        ON DELETE CASCADE,

    FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
        ON DELETE CASCADE,

    FOREIGN KEY (academic_year_id)
        REFERENCES academic_year(academic_year_id)
        ON DELETE CASCADE,

    FOREIGN KEY (assigned_by_hod)
        REFERENCES hod(hod_id)
        ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 11 : EXAM TYPE
-- ===========================================================

CREATE TABLE IF NOT EXISTS exam_type (
    exam_type_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_type_name VARCHAR(100) NOT NULL UNIQUE,
    status ENUM('Active','Inactive') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 12 : QUESTION PAPER
-- ===========================================================

CREATE TABLE IF NOT EXISTS question_paper (
    question_paper_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    exam_type_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    academic_year_id INT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    uploaded_by INT NOT NULL,
    approved_by_hod BOOLEAN DEFAULT FALSE,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assignment_id)
        REFERENCES teacher_subject_assignment(assignment_id),

    FOREIGN KEY (exam_type_id)
        REFERENCES exam_type(exam_type_id),

    FOREIGN KEY (academic_year_id)
        REFERENCES academic_year(academic_year_id),

    FOREIGN KEY (uploaded_by)
        REFERENCES teacher(teacher_id)
);


-- ===========================================================
-- TABLE 13 : STUDY MATERIAL
-- ===========================================================

CREATE TABLE IF NOT EXISTS study_material (
    study_material_id INT AUTO_INCREMENT PRIMARY KEY,
    assignment_id INT NOT NULL,
    title VARCHAR(200),
    file_name VARCHAR(255),
    uploaded_by INT NOT NULL,
    approved_by_hod BOOLEAN DEFAULT FALSE,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (assignment_id)
        REFERENCES teacher_subject_assignment(assignment_id),

    FOREIGN KEY (uploaded_by)
        REFERENCES teacher(teacher_id)
);


-- ===========================================================
-- TABLE 14 : ANSWER KEY
-- ===========================================================

CREATE TABLE IF NOT EXISTS answer_key (
    answer_key_id INT AUTO_INCREMENT PRIMARY KEY,
    question_paper_id INT NOT NULL,
    file_name VARCHAR(255),
    uploaded_by INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (question_paper_id)
        REFERENCES question_paper(question_paper_id)
        ON DELETE CASCADE,

    FOREIGN KEY (uploaded_by)
        REFERENCES teacher(teacher_id)
);


-- ===========================================================
-- TABLE 15 : EXTRACTED QUESTION
-- ===========================================================

CREATE TABLE IF NOT EXISTS extracted_question (
    extracted_question_id INT AUTO_INCREMENT PRIMARY KEY,
    question_paper_id INT NOT NULL,
    question_number VARCHAR(20),
    question_text TEXT,
    marks INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (question_paper_id)
        REFERENCES question_paper(question_paper_id)
        ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 16 : REPEATED QUESTION
-- ===========================================================

CREATE TABLE IF NOT EXISTS repeated_question (
    repeated_question_id INT AUTO_INCREMENT PRIMARY KEY,
    subject_id INT NOT NULL,
    question_text TEXT,
    repeated_count INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
        ON DELETE CASCADE
);


-- ===========================================================
-- TABLE 17 : STUDENT DOUBT
-- ===========================================================

CREATE TABLE IF NOT EXISTS student_doubt (
    doubt_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    doubt_title VARCHAR(255),
    doubt_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id)
        REFERENCES student(student_id),

    FOREIGN KEY (subject_id)
        REFERENCES subject(subject_id)
);


-- ===========================================================
-- TABLE 18 : TEACHER REPLY
-- ===========================================================

CREATE TABLE IF NOT EXISTS teacher_reply (
    reply_id INT AUTO_INCREMENT PRIMARY KEY,
    doubt_id INT NOT NULL,
    teacher_id INT NOT NULL,
    reply TEXT,
    replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (doubt_id)
        REFERENCES student_doubt(doubt_id)
        ON DELETE CASCADE,

    FOREIGN KEY (teacher_id)
        REFERENCES teacher(teacher_id)
);


-- ===========================================================
-- CHECK ALL TABLES
-- ===========================================================

SHOW TABLES;