-- ===========================================================
-- PREQABOARD DATABASE
-- COMPLETE DATABASE
-- HOD STUDENT MANAGEMENT INCLUDED
-- ===========================================================

DROP DATABASE IF EXISTS preqaboard;

CREATE DATABASE preqaboard;

USE preqaboard;


-- ===========================================================
-- TABLE 1 : DEPARTMENT
-- ===========================================================

CREATE TABLE department (

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
-- ===========================================================

CREATE TABLE course (

    course_id INT AUTO_INCREMENT PRIMARY KEY,

    department_id INT NOT NULL,

    course_name VARCHAR(100) NOT NULL,

    duration_years INT NOT NULL,

    status ENUM('Active','Inactive')
        DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_course_department

        FOREIGN KEY (department_id)

        REFERENCES department(department_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,

    UNIQUE (
        department_id,
        course_name
    )
);


-- ===========================================================
-- TABLE 3 : SEMESTER
-- ===========================================================

CREATE TABLE semester (

    semester_id INT AUTO_INCREMENT PRIMARY KEY,

    course_id INT NOT NULL,

    semester_number INT NOT NULL,

    status ENUM('Active','Inactive')
        DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_semester_course

        FOREIGN KEY (course_id)

        REFERENCES course(course_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,

    UNIQUE (
        course_id,
        semester_number
    )
);


-- ===========================================================
-- TABLE 4 : ADMIN
-- ===========================================================

CREATE TABLE admin (

    admin_id INT AUTO_INCREMENT PRIMARY KEY,

    username VARCHAR(50) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(100) NOT NULL UNIQUE,

    phone VARCHAR(15),

    status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ===========================================================
-- DEFAULT ADMIN
-- ===========================================================

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

    'scrypt:32768:8:1$CNPLf3pAYT8rSzpg$eb7734e66c7609257af2c7605e6df894464dd2147edf7ed626e0def6c4a67b0e29b362bd8ac1e5067d07c1f1d94ff64a7e8215459eb54a6d74f76c89f45cf392',

    'System Administrator',

    'admin@preqaboard.com',

    NULL,

    'Active'
);


-- ===========================================================
-- TABLE 5 : HOD
-- ===========================================================

CREATE TABLE hod (

    hod_id INT AUTO_INCREMENT PRIMARY KEY,

    department_id INT NOT NULL,

    employee_id VARCHAR(20) NOT NULL UNIQUE,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(100) NOT NULL UNIQUE,

    phone VARCHAR(15),

    username VARCHAR(50) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    account_status ENUM(
        'Pending',
        'Active',
        'Inactive'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_hod_department

        FOREIGN KEY (department_id)

        REFERENCES department(department_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 6 : TEACHER
-- ===========================================================

CREATE TABLE teacher (

    teacher_id INT AUTO_INCREMENT PRIMARY KEY,

    department_id INT NULL,

    employee_id VARCHAR(20) NOT NULL UNIQUE,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(100) NOT NULL UNIQUE,

    phone VARCHAR(15),

    username VARCHAR(50) UNIQUE,

    password VARCHAR(255),

    account_status ENUM(
        'Pending',
        'Active',
        'Inactive'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_teacher_department

        FOREIGN KEY (department_id)

        REFERENCES department(department_id)

        ON DELETE SET NULL

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 7 : STUDENT
-- ===========================================================

CREATE TABLE student (

    student_id INT AUTO_INCREMENT PRIMARY KEY,

    department_id INT NOT NULL,

    course_id INT NOT NULL,

    semester_id INT NOT NULL,

    -- CLASS / SECTION
    class_name VARCHAR(50) NOT NULL,

    register_number VARCHAR(30) NOT NULL UNIQUE,

    full_name VARCHAR(100) NOT NULL,

    email VARCHAR(100) NOT NULL UNIQUE,

    phone VARCHAR(15),

    username VARCHAR(50) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    approval_status ENUM(
        'Pending',
        'Approved',
        'Rejected'
    ) DEFAULT 'Pending',

    account_status ENUM(
        'Pending',
        'Active',
        'Inactive'
    ) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,


    CONSTRAINT fk_student_department

        FOREIGN KEY (department_id)

        REFERENCES department(department_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_student_course

        FOREIGN KEY (course_id)

        REFERENCES course(course_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_student_semester

        FOREIGN KEY (semester_id)

        REFERENCES semester(semester_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 8 : ACADEMIC YEAR
-- ===========================================================

CREATE TABLE academic_year (

    academic_year_id INT AUTO_INCREMENT PRIMARY KEY,

    academic_year_name VARCHAR(20) NOT NULL UNIQUE,

    start_date DATE NOT NULL,

    end_date DATE NOT NULL,

    status ENUM(
        'Current',
        'Completed',
        'Upcoming'
    ) DEFAULT 'Upcoming',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 9 : SYLLABUS
-- ===========================================================

CREATE TABLE syllabus (

    syllabus_id INT AUTO_INCREMENT PRIMARY KEY,

    department_id INT NOT NULL,

    course_id INT NOT NULL,

    academic_year_id INT NOT NULL,

    title VARCHAR(255) NOT NULL,

    file_name VARCHAR(255) NOT NULL,

    file_path VARCHAR(500) NOT NULL,

    uploaded_by_hod INT NOT NULL,

    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,


    CONSTRAINT fk_syllabus_department

        FOREIGN KEY (department_id)

        REFERENCES department(department_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_syllabus_course

        FOREIGN KEY (course_id)

        REFERENCES course(course_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_syllabus_academic_year

        FOREIGN KEY (academic_year_id)

        REFERENCES academic_year(academic_year_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_syllabus_hod

        FOREIGN KEY (uploaded_by_hod)

        REFERENCES hod(hod_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 10 : SUBJECT
-- ===========================================================

CREATE TABLE subject (

    subject_id INT AUTO_INCREMENT PRIMARY KEY,

    course_id INT NOT NULL,

    semester_id INT NOT NULL,

    subject_code VARCHAR(20) NOT NULL UNIQUE,

    subject_name VARCHAR(150) NOT NULL,

    credits INT DEFAULT 4,

    status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,


    CONSTRAINT fk_subject_course

        FOREIGN KEY (course_id)

        REFERENCES course(course_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_subject_semester

        FOREIGN KEY (semester_id)

        REFERENCES semester(semester_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 11 : TEACHER SUBJECT ASSIGNMENT
-- ===========================================================

CREATE TABLE teacher_subject_assignment (

    assignment_id INT AUTO_INCREMENT PRIMARY KEY,

    teacher_id INT NOT NULL,

    subject_id INT NOT NULL,

    academic_year_id INT NOT NULL,

    assigned_by_hod INT NOT NULL,

    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active',


    CONSTRAINT fk_tsa_teacher

        FOREIGN KEY (teacher_id)

        REFERENCES teacher(teacher_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_tsa_subject

        FOREIGN KEY (subject_id)

        REFERENCES subject(subject_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_tsa_academic_year

        FOREIGN KEY (academic_year_id)

        REFERENCES academic_year(academic_year_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_tsa_hod

        FOREIGN KEY (assigned_by_hod)

        REFERENCES hod(hod_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    UNIQUE (
        teacher_id,
        subject_id,
        academic_year_id
    )
);


-- ===========================================================
-- TABLE 12 : EXAM TYPE
-- ===========================================================

CREATE TABLE exam_type (

    exam_type_id INT AUTO_INCREMENT PRIMARY KEY,

    exam_type_name VARCHAR(100) NOT NULL UNIQUE,

    status ENUM(
        'Active',
        'Inactive'
    ) DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ===========================================================
-- TABLE 13 : QUESTION PAPER
-- ===========================================================

CREATE TABLE question_paper (

    question_paper_id INT AUTO_INCREMENT PRIMARY KEY,

    assignment_id INT NOT NULL,

    exam_type_id INT NOT NULL,

    title VARCHAR(200) NOT NULL,

    academic_year_id INT NOT NULL,

    file_name VARCHAR(255) NOT NULL,

    uploaded_by INT NOT NULL,

    approved_by_hod BOOLEAN DEFAULT FALSE,

    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_question_assignment

        FOREIGN KEY (assignment_id)

        REFERENCES teacher_subject_assignment(assignment_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_question_exam_type

        FOREIGN KEY (exam_type_id)

        REFERENCES exam_type(exam_type_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_question_academic_year

        FOREIGN KEY (academic_year_id)

        REFERENCES academic_year(academic_year_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_question_teacher

        FOREIGN KEY (uploaded_by)

        REFERENCES teacher(teacher_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 14 : STUDY MATERIAL
-- ===========================================================

CREATE TABLE study_material (

    study_material_id INT AUTO_INCREMENT PRIMARY KEY,

    assignment_id INT NOT NULL,

    title VARCHAR(200),

    file_name VARCHAR(255),

    uploaded_by INT NOT NULL,

    approved_by_hod BOOLEAN DEFAULT FALSE,

    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_material_assignment

        FOREIGN KEY (assignment_id)

        REFERENCES teacher_subject_assignment(assignment_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_material_teacher

        FOREIGN KEY (uploaded_by)

        REFERENCES teacher(teacher_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 15 : ANSWER KEY
-- ===========================================================

CREATE TABLE answer_key (

    answer_key_id INT AUTO_INCREMENT PRIMARY KEY,

    question_paper_id INT NOT NULL,

    file_name VARCHAR(255),

    uploaded_by INT NOT NULL,

    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_answer_question

        FOREIGN KEY (question_paper_id)

        REFERENCES question_paper(question_paper_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_answer_teacher

        FOREIGN KEY (uploaded_by)

        REFERENCES teacher(teacher_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 16 : EXTRACTED QUESTION
-- ===========================================================

CREATE TABLE extracted_question (

    extracted_question_id INT AUTO_INCREMENT PRIMARY KEY,

    question_paper_id INT NOT NULL,

    question_number VARCHAR(20),

    question_text TEXT,

    marks INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_extracted_question_paper

        FOREIGN KEY (question_paper_id)

        REFERENCES question_paper(question_paper_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 17 : REPEATED QUESTION
-- ===========================================================

CREATE TABLE repeated_question (

    repeated_question_id INT AUTO_INCREMENT PRIMARY KEY,

    subject_id INT NOT NULL,

    question_text TEXT,

    repeated_count INT DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_repeated_subject

        FOREIGN KEY (subject_id)

        REFERENCES subject(subject_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 18 : STUDENT DOUBT
-- ===========================================================

CREATE TABLE student_doubt (

    doubt_id INT AUTO_INCREMENT PRIMARY KEY,

    student_id INT NOT NULL,

    subject_id INT NOT NULL,

    doubt_title VARCHAR(255),

    doubt_description TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_doubt_student

        FOREIGN KEY (student_id)

        REFERENCES student(student_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_doubt_subject

        FOREIGN KEY (subject_id)

        REFERENCES subject(subject_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 19 : TEACHER REPLY
-- ===========================================================

CREATE TABLE teacher_reply (

    reply_id INT AUTO_INCREMENT PRIMARY KEY,

    doubt_id INT NOT NULL,

    teacher_id INT NOT NULL,

    reply TEXT,

    replied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,


    CONSTRAINT fk_reply_doubt

        FOREIGN KEY (doubt_id)

        REFERENCES student_doubt(doubt_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_reply_teacher

        FOREIGN KEY (teacher_id)

        REFERENCES teacher(teacher_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 20 : ASSIGNMENT
-- ===========================================================

CREATE TABLE assignment (

    assignment_id INT AUTO_INCREMENT PRIMARY KEY,

    assignment_name VARCHAR(200) NOT NULL,

    description TEXT,

    assignment_type VARCHAR(100),

    assignment_file VARCHAR(255),

    assignment_date DATE NOT NULL,

    due_date DATE NOT NULL,

    teacher_subject_assignment_id INT NOT NULL,

    academic_year_id INT NOT NULL,

    uploaded_by INT NOT NULL,

    status ENUM(
        'Active',
        'Inactive',
        'Closed'
    ) DEFAULT 'Active',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,


    CONSTRAINT fk_assignment_tsa

        FOREIGN KEY (teacher_subject_assignment_id)

        REFERENCES teacher_subject_assignment(assignment_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_assignment_academic_year

        FOREIGN KEY (academic_year_id)

        REFERENCES academic_year(academic_year_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_assignment_teacher

        FOREIGN KEY (uploaded_by)

        REFERENCES teacher(teacher_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE
);


-- ===========================================================
-- TABLE 21 : ASSIGNMENT SUBMISSION
-- ===========================================================

CREATE TABLE assignment_submission (

    submission_id INT AUTO_INCREMENT PRIMARY KEY,

    assignment_id INT NOT NULL,

    student_id INT NOT NULL,

    file_name VARCHAR(255),

    submission_text TEXT,

    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    marks DECIMAL(5,2),

    feedback TEXT,

    status ENUM(
        'Submitted',
        'Late',
        'Checked',
        'Returned'
    ) DEFAULT 'Submitted',


    CONSTRAINT fk_submission_assignment

        FOREIGN KEY (assignment_id)

        REFERENCES assignment(assignment_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    CONSTRAINT fk_submission_student

        FOREIGN KEY (student_id)

        REFERENCES student(student_id)

        ON DELETE CASCADE

        ON UPDATE CASCADE,


    UNIQUE (
        assignment_id,
        student_id
    )
);


-- ===========================================================
-- INDEXES
-- ===========================================================


-- COURSE

CREATE INDEX idx_course_department
ON course(department_id);


-- SEMESTER

CREATE INDEX idx_semester_course
ON semester(course_id);


-- HOD

CREATE INDEX idx_hod_department
ON hod(department_id);


-- TEACHER

CREATE INDEX idx_teacher_department
ON teacher(department_id);


-- ===========================================================
-- STUDENT INDEXES
-- ===========================================================

CREATE INDEX idx_student_department
ON student(department_id);


CREATE INDEX idx_student_course
ON student(course_id);


CREATE INDEX idx_student_semester
ON student(semester_id);


CREATE INDEX idx_student_class
ON student(class_name);


CREATE INDEX idx_student_approval
ON student(approval_status);


CREATE INDEX idx_student_account_status
ON student(account_status);


CREATE INDEX idx_student_name
ON student(full_name);


CREATE INDEX idx_student_register
ON student(register_number);


CREATE INDEX idx_student_department_course_semester_class
ON student(
    department_id,
    course_id,
    semester_id,
    class_name
);


-- ===========================================================
-- SYLLABUS INDEXES
-- ===========================================================

CREATE INDEX idx_syllabus_department
ON syllabus(department_id);


CREATE INDEX idx_syllabus_course
ON syllabus(course_id);


CREATE INDEX idx_syllabus_academic_year
ON syllabus(academic_year_id);


CREATE INDEX idx_syllabus_hod
ON syllabus(uploaded_by_hod);


CREATE INDEX idx_syllabus_uploaded_at
ON syllabus(uploaded_at);


CREATE INDEX idx_syllabus_status
ON syllabus(status);


-- ===========================================================
-- SUBJECT INDEXES
-- ===========================================================

CREATE INDEX idx_subject_course
ON subject(course_id);


CREATE INDEX idx_subject_semester
ON subject(semester_id);


-- ===========================================================
-- TEACHER SUBJECT ASSIGNMENT INDEXES
-- ===========================================================

CREATE INDEX idx_tsa_teacher
ON teacher_subject_assignment(teacher_id);


CREATE INDEX idx_tsa_subject
ON teacher_subject_assignment(subject_id);


CREATE INDEX idx_tsa_hod
ON teacher_subject_assignment(assigned_by_hod);


-- ===========================================================
-- QUESTION PAPER INDEXES
-- ===========================================================

CREATE INDEX idx_question_paper_teacher
ON question_paper(uploaded_by);


CREATE INDEX idx_question_paper_assignment
ON question_paper(assignment_id);


-- ===========================================================
-- STUDY MATERIAL INDEXES
-- ===========================================================

CREATE INDEX idx_study_material_teacher
ON study_material(uploaded_by);


CREATE INDEX idx_study_material_assignment
ON study_material(assignment_id);


-- ===========================================================
-- ASSIGNMENT INDEXES
-- ===========================================================

CREATE INDEX idx_assignment_teacher
ON assignment(uploaded_by);


CREATE INDEX idx_assignment_tsa
ON assignment(teacher_subject_assignment_id);


CREATE INDEX idx_assignment_academic_year
ON assignment(academic_year_id);


-- ===========================================================
-- SUBMISSION INDEXES
-- ===========================================================

CREATE INDEX idx_submission_assignment
ON assignment_submission(assignment_id);


CREATE INDEX idx_submission_student
ON assignment_submission(student_id);


-- ===========================================================
-- DOUBT INDEXES
-- ===========================================================

CREATE INDEX idx_doubt_student
ON student_doubt(student_id);


CREATE INDEX idx_doubt_subject
ON student_doubt(subject_id);


-- ===========================================================
-- REPLY INDEXES
-- ===========================================================

CREATE INDEX idx_reply_teacher
ON teacher_reply(teacher_id);


CREATE INDEX idx_reply_doubt
ON teacher_reply(doubt_id);


-- ===========================================================
-- SAMPLE / OPTIONAL DATA
-- ===========================================================

-- You can add your actual departments later.

-- Example:

-- INSERT INTO department
-- (department_name)
-- VALUES
-- ('Computer Applications');


-- ===========================================================
-- VERIFICATION
-- ===========================================================

SHOW TABLES;


-- ===========================================================
-- VERIFY STUDENT TABLE
-- ===========================================================

DESCRIBE student;


-- ===========================================================
-- VERIFY STUDENT DATA
-- ===========================================================

SELECT
    s.student_id,
    d.department_name,
    c.course_name,
    sem.semester_number,
    s.class_name,
    s.register_number,
    s.full_name,
    s.email,
    s.phone,
    s.username,
    s.approval_status,
    s.account_status,
    s.created_at,
    s.updated_at

FROM student s

INNER JOIN department d
    ON s.department_id = d.department_id

INNER JOIN course c
    ON s.course_id = c.course_id

INNER JOIN semester sem
    ON s.semester_id = sem.semester_id

ORDER BY
    c.course_name,
    sem.semester_number,
    s.class_name,
    s.full_name;


-- ===========================================================
-- VERIFY HOD -> DEPARTMENT
-- ===========================================================

SELECT
    h.hod_id,
    h.employee_id,
    h.full_name,
    h.email,
    h.username,
    d.department_name,
    h.account_status

FROM hod h

INNER JOIN department d
    ON h.department_id = d.department_id;


-- ===========================================================
-- VERIFY SYLLABUS
-- ===========================================================

DESCRIBE syllabus;


-- ===========================================================
-- VERIFY SYLLABUS DATA
-- ===========================================================

SELECT
    syllabus_id,
    department_id,
    course_id,
    academic_year_id,
    title,
    file_name,
    file_path,
    uploaded_by_hod,
    uploaded_at,
    status,
    created_at,
    updated_at

FROM syllabus;


-- ===========================================================
-- END OF DATABASE
-- ===========================================================