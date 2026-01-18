-- Drop existing tables to ensure a clean slate on re-initialization
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS faculty;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS feedback;

-- Create all necessary tables for the application

CREATE TABLE students (
    id TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    class TEXT NOT NULL
);

CREATE TABLE faculty (
    id TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE teachers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT,
    teacher_id TEXT,
    semester TEXT,
    q1 INTEGER, q2 INTEGER, q3 INTEGER, q4 INTEGER, q5 INTEGER,
    q6 INTEGER, q7 INTEGER, q8 INTEGER, q9 INTEGER, q10 INTEGER,
    comments TEXT,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

-- Insert initial data into the tables

-- Student data
INSERT INTO students (id, password, name, class) VALUES
('24D01', 'password123', 'Aslam Mumin Muhammad Farida', 'S.Y. B.Sc. DS'),
('24D02', 'password123', 'Balbale Affaan Arif Fatima', 'S.Y. B.Sc. DS'),
('24D03', 'password123', 'Barne Sanchit Ganesh Shital', 'S.Y. B.Sc. DS'),
('24D04', 'password123', 'Bhadrike Sakshi Sachin Sanjana', 'S.Y. B.Sc. DS'),
('24D05', 'password123', 'Chaugule Taiba Ikbal Samina', 'S.Y. B.Sc. DS'),
('24D06', 'password123', 'Chawan Tanmay', 'S.Y. B.Sc. DS'),
('24D07', 'password123', 'Desai Saloni Sunil Smita', 'S.Y. B.Sc. DS'),
('24D08', 'password123', 'Devadiga Samiksha Ravi Vishalaksh', 'S.Y. B.Sc. DS'),
('24D09', 'password123', 'Dhamale Ketaki Kumar Seema', 'S.Y. B.Sc. DS'),
('24D10', 'password123', 'Dighe Sakshi Vijay Sangita', 'S.Y. B.Sc. DS'),
('24D11', 'password123', 'Dive Lavanya A', 'S.Y. B.Sc. DS'),
('21CS001', 'password123', 'Rohan Sharma', 'T.Y. B.Sc. CS'),
('21IT015', 'password123', 'Priya Singh', 'T.Y. B.Sc. IT');

-- UPDATED Faculty and HOD data
-- Only HOD needs login access to the dashboard
INSERT INTO faculty (id, password, name, role) VALUES
('hod_ds', 'hod_pass', 'Dr. Nutan Sawant', 'hod');

-- UPDATED Teacher data for student review
-- All three faculty members are available for students to provide feedback on
INSERT INTO teachers (id, name) VALUES
('prof_ns', 'Dr. Nutan Sawant'),
('prof_vs', 'Ms. Varsha Shinde'),
('prof_rp', 'Ms. Rashmi Prabha');