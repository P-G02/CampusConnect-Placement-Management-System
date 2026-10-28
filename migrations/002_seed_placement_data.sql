-- =============================================================
-- CampusConnect: Seed placement data (safe to re-run)
-- Inserts only if records don't already exist
-- =============================================================

-- Departments
INSERT INTO department (dept_id, dept_name) VALUES
('A1001', 'Computer Science'),
('A1002', 'Electronics Engineering'),
('A1003', 'Mechanical Engineering'),
('A1004', 'Information Technology'),
('A1005', 'Data Science'),
('A1006', 'Electrical Engineering')
ON CONFLICT (dept_id) DO NOTHING;

-- Students
INSERT INTO student (student_id, student_name, student_email, student_phone, dept_id, cgpa, graduation_yr) VALUES
('S1001', 'Shah Rukh Khan', 'srk_0211@gmail.com', '9876500001', 'A1001', 7.65, 2027),
('S1002', 'Deepika Padukone', 'deepika@gmail.com', '9876500002', 'A1001', 8.80, 2029),
('S1003', 'Priyanka Chopra', 'pcj@gmail.com', '9876500003', 'A1002', 9.76, 2028),
('S1004', 'Tom Cruise', 'mission_impossible@gmail.com', '9876500004', 'A1002', 7.20, 2027),
('S1005', 'Leonardo DiCaprio', 'leo.11@gmail.com', '9876500005', 'A1003', 6.33, 2027),
('S1006', 'Virat Kohli', 'chase.master.18@gmail.com', '9876500006', 'A1003', 9.00, 2028),
('S1007', 'Akshay Kumar', 'khiladi.404@gmail.com', '9876500007', 'A1004', 8.15, 2027),
('S1008', 'Tom Holland', 'spiderman@gmail.com', '9876500008', 'A1004', 7.17, 2030),
('S1009', 'Margot Robbie', 'barbie.in.debug.mode@gmail.com', '9876500009', 'A1005', 9.32, 2029),
('S1010', 'Abhishek Sharma', 'sixer@gmail.com', '9876500010', 'A1005', 9.10, 2030),
('S1011', 'Johnny Depp', 'captain_jack_sparrow@gmail.com', '9876500011', 'A1006', 6.85, 2027),
('S1012', 'Robert Downey Jr.', 'i.am.iron.man@gmail.com', '9876500012', 'A1006', 8.33, 2028)
ON CONFLICT (student_id) DO NOTHING;

-- Companies
INSERT INTO company (company_id, company_name, company_email, company_phone, company_locn) VALUES
('C10001', 'Tata Consultancy Services', 'tcs@careers.example.com', '9100000001', 'Mumbai'),
('C10012', 'Infosys', 'campus@infosys.example.com', '9100000002', 'Bengaluru'),
('C10135', 'Serum Institute of India', 'hr@serum.example.com', '9100000035', 'Pune'),
('C10333', 'Wipro', 'hiring@wipro.example.com', '9100000003', 'Bengaluru'),
('C10540', 'HCL Technologies', 'jobs@hcl.example.com', '9100000004', 'Noida'),
('C10555', 'Tech Mahindra', 'talent@techm.example.com', '9100000005', 'Pune'),
('C10626', 'Accenture', 'campus@accenture.example.com', '9100000006', 'Hyderabad'),
('C10749', 'Capgemini', 'recruit@capgemini.example.com', '9100000007', 'Mumbai'),
('C10842', 'Reliance India', 'campus@jio.example.com', '9100000008', 'Mumbai'),
('C10913', 'Deloitte India', 'campus@deloitte.example.com', '9100000013', 'Gurugram')
ON CONFLICT (company_id) DO NOTHING;

-- Opportunities
INSERT INTO opportunity (opp_id, company_id, opp_title, opp_type, opp_locn, stipend, package, min_cgpa, deadline) VALUES
('O10001', 'C10001', 'Assistant System Engineer', 'JOB', 'Mumbai', NULL, 450000.00, 7.60, '2026-11-15'),
('O10002', 'C10012', 'Systems Engineer', 'JOB', 'Bengaluru', NULL, 400000.00, 7.60, '2026-11-20'),
('O10003', 'C10012', 'Project Engineer', 'JOB', 'Bengaluru', NULL, 380000.00, 7.70, '2026-11-20'),
('O10004', 'C10135', 'Bioprocess Intern', 'INTERNSHIP', 'Pune', 18000.00, NULL, 7.60, '2026-11-28'),
('O10005', 'C10333', 'Software Development Engineer', 'JOB', 'Bengaluru', NULL, 2200000.00, 8.50, '2026-12-15'),
('O10006', 'C10540', 'Mechanical Design Engineer', 'JOB', 'Bengaluru', NULL, 700000.00, 8.00, '2026-12-18'),
('O10007', 'C10555', 'Data Science Intern', 'INTERNSHIP', 'Mumbai', 30000.00, NULL, 8.00, '2026-11-22'),
('O10008', 'C10626', 'Software Engineer Intern', 'INTERNSHIP', 'Hyderabad', 100000.00, NULL, 9.00, '2026-11-10'),
('O10009', 'C10749', 'Product Engineering Intern', 'INTERNSHIP', 'Mumbai', 50000.00, NULL, 8.50, '2026-11-18'),
('O10010', 'C10842', 'Telecom Software Engineer', 'JOB', 'Mumbai', NULL, 850000.00, 8.30, '2026-12-28'),
('O10011', 'C10913', 'AI Research Intern', 'INTERNSHIP', 'Gurugram', 40000.00, NULL, 8.80, '2026-11-30')
ON CONFLICT (opp_id) DO NOTHING;

-- Skills
INSERT INTO skill (skill_id, skill_name) VALUES
('K10001', 'C Programming'), ('K10002', 'Java'), ('K10003', 'Python'), ('K10004', 'JavaScript'),
('K10005', 'SQL'), ('K10006', 'Data Structures'), ('K10007', 'Algorithms'),
('K10008', 'HTML and CSS'), ('K10009', 'Cloud Computing'), ('K10010', 'Git and Github'),
('K10011', 'Data Analytics'), ('K10012', 'Machine Learning'), ('K10013', 'Operating Systems'),
('K10014', 'Embedded Systems'), ('K10015', 'AutoCAD'), ('K10016', 'SolidWorks'),
('K10017', 'Bioinformatics'), ('K10018', 'Communication skills')
ON CONFLICT (skill_id) DO NOTHING;

-- Student skills
INSERT INTO student_skill (student_id, skill_id) VALUES
('S1001', 'K10001'), ('S1001', 'K10002'), ('S1001', 'K10003'),
('S1002', 'K10002'), ('S1002', 'K10003'), ('S1002', 'K10004'),
('S1003', 'K10003'), ('S1003', 'K10004'), ('S1003', 'K10005'), ('S1003', 'K10006'), ('S1003', 'K10007'), ('S1003', 'K10011'), ('S1003', 'K10012'),
('S1004', 'K10004'), ('S1004', 'K10005'), ('S1004', 'K10006'),
('S1005', 'K10005'), ('S1005', 'K10006'),
('S1006', 'K10005'), ('S1006', 'K10006'), ('S1006', 'K10007'),
('S1007', 'K10007'), ('S1007', 'K10008'),
('S1008', 'K10008'),
('S1009', 'K10006'), ('S1009', 'K10007'), ('S1009', 'K10008'), ('S1009', 'K10009'),
('S1010', 'K10006'), ('S1010', 'K10007'), ('S1010', 'K10008'), ('S1010', 'K10009'), ('S1010', 'K10010'),
('S1011', 'K10011'), ('S1011', 'K10012'), ('S1011', 'K10013'),
('S1012', 'K10014'), ('S1012', 'K10015'), ('S1012', 'K10016'), ('S1012', 'K10017')
ON CONFLICT DO NOTHING;

-- Applications
INSERT INTO application (appl_id, student_id, opp_id, appl_date) VALUES
('AP10001','S1001','O10001','2026-10-05'),
('AP10002','S1001','O10002','2026-10-06'),
('AP10003','S1002','O10005','2026-10-07'),
('AP10004','S1002','O10007','2026-10-08'),
('AP10005','S1002','O10011','2026-10-09'),
('AP10006','S1003','O10008','2026-10-03'),
('AP10007','S1003','O10010','2026-10-04'),
('AP10008','S1006','O10008','2026-10-10'),
('AP10009','S1006','O10010','2026-10-11'),
('AP10010','S1007','O10006','2026-10-12')
ON CONFLICT (appl_id) DO NOTHING;

-- Interviews
INSERT INTO interview (interview_id, appl_id, interview_date, interview_rd, status) VALUES
('IN10001', 'AP10001', '2026-10-12 10:00:00', 2, 'CLEARED'),
('IN10002', 'AP10002', '2026-10-15 11:30:00', 1, 'SCHEDULED'),
('IN10003', 'AP10003', '2026-10-22 10:00:00', 1, 'REJECTED'),
('IN10004', 'AP10004', '2026-10-18 10:30:00', 3, 'CLEARED'),
('IN10005', 'AP10005', '2026-10-15 13:00:00', 2, 'SCHEDULED'),
('IN10006', 'AP10006', '2026-10-16 11:00:00', 1, 'REJECTED'),
('IN10007', 'AP10007', '2026-10-21 11:00:00', 1, 'CLEARED'),
('IN10008', 'AP10008', '2026-10-21 11:00:00', 3, 'SCHEDULED'),
('IN10009', 'AP10009', '2026-10-21 11:00:00', 2, 'REJECTED'),
('IN10010', 'AP10007', '2026-10-21 11:00:00', 1, 'CLEARED')
ON CONFLICT (interview_id) DO NOTHING;

-- Placements (actual columns: plm_id, plm_date — no interview_id FK)
INSERT INTO placement (plm_id, student_id, company_id, opp_id, package, plm_date) VALUES
('PL10001', 'S1001', 'C10001', 'O10001', 450000.00, '2026-10-14'),
('PL10002', 'S1002', 'C10555', 'O10007', NULL, '2026-10-19'),
('PL10003', 'S1003', 'C10842', 'O10010', 850000.00, '2026-10-22')
ON CONFLICT (plm_id) DO NOTHING;
