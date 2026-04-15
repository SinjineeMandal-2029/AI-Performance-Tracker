USE edutrack_db;

-- SUBJECT ENROLLMENTS

INSERT INTO enrollments (student_id, subject_id)
VALUES
(2,1),
(2,2),
(2,3),
(2,4),
(2,5);

-- GRADES DATA

INSERT INTO grades (
    student_id,
    subject_id,
    exam_type,
    marks_obtained,
    max_marks,
    date
)
VALUES
(2,1,'quiz',88,100,'2026-03-24'),
(2,2,'assignment',80,100,'2026-03-23'),
(2,3,'midterm',90,100,'2026-03-22'),
(2,4,'quiz',72,100,'2026-03-21'),
(2,5,'quiz',85,100,'2026-03-20');


-- ATTENDANCE DATA

INSERT INTO attendance (
    student_id,
    subject_id,
    date,
    status
)
VALUES
(2,1,'2026-03-01','present'),
(2,1,'2026-03-02','present'),
(2,2,'2026-03-01','absent'),
(2,2,'2026-03-02','present'),
(2,3,'2026-03-03','present'),
(2,4,'2026-03-04','present'),
(2,5,'2026-03-05','present');

-- ASSIGNMENT SUBMISSIONS

INSERT INTO submissions (
    assignment_id,
    student_id,
    status
)
VALUES
(1,2,'pending'),
(2,2,'pending'),
(3,2,'pending');

-- OPTIONAL EXTRA DEMO DATA
INSERT INTO grades (
    student_id,
    subject_id,
    exam_type,
    marks_obtained,
    max_marks,
    date
)
VALUES
(2,1,'final',92,100,'2026-03-28'),
(2,2,'quiz',84,100,'2026-03-27');

INSERT INTO attendance (
    student_id,
    subject_id,
    date,
    status
)
VALUES
(2,3,'2026-03-06','present'),
(2,4,'2026-03-07','present');