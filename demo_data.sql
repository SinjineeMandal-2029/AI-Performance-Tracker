-- Demo data for the FIRST student account (sign up on the live site first, then run this)

SET @sid = (SELECT id FROM students ORDER BY id LIMIT 1);

INSERT IGNORE INTO enrollments (student_id, subject_id) VALUES
(@sid,1),(@sid,2),(@sid,3),(@sid,4),(@sid,5);

INSERT INTO grades (student_id, subject_id, exam_type, marks_obtained, max_marks, date) VALUES
(@sid,1,'quiz',88,100,'2026-03-24'),
(@sid,2,'assignment',80,100,'2026-03-23'),
(@sid,3,'midterm',90,100,'2026-03-22'),
(@sid,4,'quiz',72,100,'2026-03-21'),
(@sid,5,'quiz',85,100,'2026-03-20'),
(@sid,1,'final',92,100,'2026-03-28'),
(@sid,2,'quiz',84,100,'2026-03-27');

INSERT IGNORE INTO attendance (student_id, subject_id, date, status) VALUES
(@sid,1,'2026-03-01','present'),
(@sid,1,'2026-03-02','present'),
(@sid,2,'2026-03-01','absent'),
(@sid,2,'2026-03-02','present'),
(@sid,3,'2026-03-03','present'),
(@sid,3,'2026-03-06','present'),
(@sid,4,'2026-03-04','present'),
(@sid,4,'2026-03-07','present'),
(@sid,5,'2026-03-05','present');
