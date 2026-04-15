-- ============================================================
-- EduTrack AI — MySQL Database Schema
-- Run: mysql -u root -p < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS edutrack_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE edutrack_db;

-- ── USERS ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id            INT PRIMARY KEY AUTO_INCREMENT,
    name          VARCHAR(255)    NOT NULL,
    email         VARCHAR(255)    UNIQUE NOT NULL,
    password_hash VARCHAR(255)    NOT NULL,
    role          ENUM('student','teacher','parent','admin') NOT NULL,
    is_active     BOOLEAN         DEFAULT TRUE,
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role  (role)
);

-- ── STUDENTS ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS students (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    user_id     INT         NOT NULL UNIQUE,
    student_id  VARCHAR(50) UNIQUE NOT NULL,
    semester    INT         DEFAULT 1,
    department  VARCHAR(100),
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_student_user (user_id)
);

-- ── TEACHERS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teachers (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    user_id     INT         NOT NULL UNIQUE,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    department  VARCHAR(100),
    created_at  TIMESTAMP   DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_teacher_user (user_id)
);

-- ── PARENT–STUDENT LINK ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS parent_student (
    parent_user_id  INT NOT NULL,
    student_user_id INT NOT NULL,
    PRIMARY KEY (parent_user_id, student_user_id),
    FOREIGN KEY (parent_user_id)  REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (student_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ── SUBJECTS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS subjects (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(150) NOT NULL,
    code        VARCHAR(30)  UNIQUE NOT NULL,
    credits     INT          DEFAULT 3,
    semester    INT          DEFAULT 1,
    department  VARCHAR(100),
    teacher_id  INT,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE SET NULL,
    INDEX idx_teacher (teacher_id)
);

-- ── ENROLLMENTS ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS enrollments (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    student_id  INT NOT NULL,
    subject_id  INT NOT NULL,
    semester    INT DEFAULT 1,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_enrollment (student_id, subject_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- ── GRADES ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS grades (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    student_id     INT            NOT NULL,
    subject_id     INT            NOT NULL,
    exam_type      ENUM('quiz','midterm','final','assignment') NOT NULL,
    marks_obtained DECIMAL(6,2)   NOT NULL,
    max_marks      DECIMAL(6,2)   NOT NULL DEFAULT 100,
    remarks        VARCHAR(255),
    date           DATE           NOT NULL,
    created_at     TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id)  ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id)  ON DELETE CASCADE,
    INDEX idx_grade_student (student_id),
    INDEX idx_grade_subject (subject_id)
);

-- ── ATTENDANCE ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS attendance (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    student_id  INT  NOT NULL,
    subject_id  INT  NOT NULL,
    date        DATE NOT NULL,
    status      ENUM('present','absent','late') NOT NULL DEFAULT 'present',
    marked_by   INT,  -- teacher user_id
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_attendance (student_id, subject_id, date),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    INDEX idx_attend_student (student_id),
    INDEX idx_attend_date    (date)
);

-- ── ASSIGNMENTS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS assignments (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    subject_id  INT          NOT NULL,
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    due_date    DATE         NOT NULL,
    max_marks   DECIMAL(6,2) DEFAULT 100,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    INDEX idx_assign_subject (subject_id),
    INDEX idx_assign_due     (due_date)
);

-- ── SUBMISSIONS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS submissions (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    assignment_id  INT         NOT NULL,
    student_id     INT         NOT NULL,
    submitted_at   TIMESTAMP   NULL,
    marks_obtained DECIMAL(6,2),
    feedback       TEXT,
    status         ENUM('pending','submitted','graded','late') DEFAULT 'pending',
    UNIQUE KEY uq_submission (assignment_id, student_id),
    FOREIGN KEY (assignment_id) REFERENCES assignments(id) ON DELETE CASCADE,
    FOREIGN KEY (student_id)    REFERENCES students(id)    ON DELETE CASCADE,
    INDEX idx_sub_student (student_id)
);

-- ── AI PREDICTIONS (CACHE) ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id              INT PRIMARY KEY AUTO_INCREMENT,
    student_id      INT          NOT NULL,
    subject_id      INT,
    predicted_score DECIMAL(5,2),
    predicted_grade VARCHAR(5),
    predicted_gpa   DECIMAL(4,2),
    confidence      DECIMAL(5,2),
    suggestions     JSON,
    generated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE SET NULL,
    INDEX idx_pred_student (student_id)
);

-- ── SAMPLE DATA ───────────────────────────────────────────────────────────────
-- Default admin user (password: Admin@1234)
INSERT IGNORE INTO users (name, email, password_hash, role) VALUES
('Admin', 'admin@university.edu',
 '$2b$12$placeholder_hash_replace_with_bcrypt', 'admin');

-- Sample subjects
INSERT IGNORE INTO subjects (name, code, credits, semester, department) VALUES
('Data Structures & Algorithms', 'CSE301', 4, 3, 'Computer Science'),
('Mathematics III',              'MAT301', 3, 3, 'Mathematics'),
('Database Management Systems',  'CSE302', 3, 3, 'Computer Science'),
('Operating Systems',            'CSE303', 3, 3, 'Computer Science'),
('Web Development',              'CSE304', 3, 3, 'Computer Science');

-- ── VIEWS ─────────────────────────────────────────────────────────────────────
-- Student performance summary view
CREATE OR REPLACE VIEW student_performance_summary AS
SELECT
    u.id          AS user_id,
    u.name        AS student_name,
    s.student_id,
    s.semester,
    s.department,
    sub.name      AS subject,
    ROUND(AVG(g.marks_obtained / g.max_marks * 100), 2) AS avg_pct,
    ROUND(
        SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) /
        NULLIF(COUNT(DISTINCT a.id), 0) * 100, 2
    ) AS attend_pct
FROM users u
JOIN students s ON s.user_id = u.id
JOIN enrollments e ON e.student_id = s.id
JOIN subjects sub ON sub.id = e.subject_id
LEFT JOIN grades g ON g.student_id = s.id AND g.subject_id = sub.id
LEFT JOIN attendance a ON a.student_id = s.id AND a.subject_id = sub.id
WHERE u.role = 'student'
GROUP BY u.id, sub.id;