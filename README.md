# ET-DMS (ET Department Management System)

```Abstract```

If students want to view their past results, or view their attendance, there is no easy accessibility and they have to navigate through many links and documents on the college website. Additionally, for faculty, applying for leave and managing the classes or the results of examinations requires a lot of manual documentation which can be repetitive and time taking. Furthermore, the HOD will need to view an overview of all the student details of the department, which would normally require the HOD to manage multiple databases for each functionality.

Therefore, I propose a Department Management System which includes three interfaces for each type of users, they are HOD, Staff, and Student. Students can view their Attendance and Midterm Marks. Staff can add Student Attendance, Midterm marks and Assignment marks, download report of Students Marks and Attendance and apply for Leave. HOD can view and download Student Attendance and Mid-term results based on class, and also approve faculty leave. The system will automatically downscale the Mid-term marks.

```Technologies Used```

- django (python)
- html, css, javascript
- sqlite
- SheetJS
- pdfMake
- jQuery
- ajax
- bootstrap

```Features```
1. automatic downscaling of midterm marks
2. automatic attendance marks calculation for internal
3. report generation for attendance and internal marks (download as Excel or PDF)
4. leave application for staff (with automatic CL calculation)

```Notes```
- this project was developed as a final year project for UG
- based on an existing college management system project and enhanced to add additional features
- you must first login to admin and create all the necessary objects (Semester, Subject, Branch, Staff, Student, etc) before logging in. 
- only the admin credentials have been created.

```Admin credentials:```

**email:** admin@gmail.com

**password:** root
