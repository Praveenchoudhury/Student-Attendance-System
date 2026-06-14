========================================================
  STUDENT INFORMATION & ATTENDANCE SYSTEM
  README — Plain Text Version
========================================================

PROJECT NAME   : Student Information & Attendance System
STACK          : Python (Flask) + HTML + CSS + SQLite
VERSION        : 1.0
LICENSE        : Free to use for educational purposes


--------------------------------------------------------
TABLE OF CONTENTS
--------------------------------------------------------
  1. Overview
  2. Features
  3. Requirements
  4. Folder Structure
  5. How to Run Locally (VS Code / Terminal)
  6. How to Use the App
  7. Where is the Data Stored?
  8. CSV Export
  9. Dark Mode
 10. Troubleshooting
 11. Future Improvements


--------------------------------------------------------
1. OVERVIEW
--------------------------------------------------------
This is a web-based Student Information and Attendance
Management System built for schools and colleges.

Teachers can manage student records, mark daily
attendance, view reports, and export CSV files.
Students can log in with their Roll No and a PIN to
view their own attendance record and download it.

The app runs entirely on your local machine — no
internet connection is needed after setup.


--------------------------------------------------------
2. FEATURES
--------------------------------------------------------
TEACHER (blank login — just click Login as Teacher):
  - Dashboard with total students, classes,
    today's attendance count, and a 7-day trend chart.
  - Add / Edit / Delete student records.
  - Set a login PIN for each student.
  - Mark daily attendance (Present / Absent / Late)
    for all students or by class.
  - Bulk mark all students Present or Absent.
  - View attendance summary report by date range.
  - View per-student attendance history.
  - Download attendance reports as CSV files.

STUDENT (login with Roll No + PIN):
  - View personal profile and details.
  - View own attendance record with date filter.
  - See attendance % and summary (Present/Absent/Late).
  - Download own attendance as a CSV file.

GENERAL:
  - Light / Dark mode toggle (top-right corner, any page).
  - Fully responsive — works on phones and tablets too.
  - No internet required after installation.


--------------------------------------------------------
3. REQUIREMENTS
--------------------------------------------------------
  - Python 3.8 or higher
    Download: https://www.python.org/downloads/
    (Tick "Add Python to PATH" during installation)

  - Flask (Python library)
    Installed via requirements.txt (see Step 5)

  - A modern web browser:
    Chrome, Edge, Firefox, or Safari


--------------------------------------------------------
4. FOLDER STRUCTURE
--------------------------------------------------------
  student-attendance-system/
  |
  |-- app.py               Main Python application
  |-- requirements.txt     Python dependencies
  |
  |-- templates/           HTML pages
  |   |-- base.html        Base layout (dark mode script)
  |   |-- _shell.html      Sidebar + navigation shell
  |   |-- login.html       Login page
  |   |-- dashboard.html   Teacher dashboard
  |   |-- students_list.html    Student list + search
  |   |-- students_add.html     Add new student form
  |   |-- students_edit.html    Edit student form
  |   |-- attendance.html       Mark daily attendance
  |   |-- reports_summary.html  Summary report by date
  |   |-- reports_history.html  Per-student history
  |   |-- profile.html          Student: my profile
  |   |-- my_attendance.html    Student: my attendance
  |
  |-- static/
  |   |-- styles.css       All styles (light + dark mode)
  |
  |-- data/                Created automatically on first run
      |-- school.db        SQLite database (all your data)


--------------------------------------------------------
5. HOW TO RUN LOCALLY (VS CODE / TERMINAL)
--------------------------------------------------------

STEP 1 — Install Python
  Download from https://www.python.org/downloads/
  During installation, CHECK "Add Python to PATH".

STEP 2 — Extract the project
  Unzip the downloaded file.
  You will get a folder called "student-attendance-system".

STEP 3 — Open in VS Code
  File > Open Folder > select "student-attendance-system"

STEP 4 — Open a terminal
  In VS Code: Terminal > New Terminal  (or Ctrl + `)

STEP 5 — Install Flask
  Type this command and press Enter:

    pip install -r requirements.txt

  If pip is not found, try:
    python -m pip install -r requirements.txt       (Windows)
    python3 -m pip install -r requirements.txt      (Mac/Linux)

STEP 6 — Start the app
  Type this command and press Enter:

    python app.py             (Windows)
    python3 app.py            (Mac / Linux)

  You will see a message like:
    * Running on http://0.0.0.0:5000

STEP 7 — Open your browser
  Go to:  http://localhost:5000

STEP 8 — Stop the server
  Press Ctrl + C in the terminal.


ALTERNATIVE — run without VS Code:
  1. Open Command Prompt (Windows) or Terminal (Mac/Linux).
  2. Navigate to the project folder:
       cd path\to\student-attendance-system
  3. Run steps 5 and 6 above.


--------------------------------------------------------
6. HOW TO USE THE APP
--------------------------------------------------------

AS A TEACHER:
  1. Go to http://localhost:5000
  2. Select "Teacher" tab.
  3. Click "Login as Teacher" (no username/password needed).
  4. Go to "Students" > "Add Student" to add students.
     - Roll No, Name, Class, and PIN are required.
     - The PIN is what the student uses to log in.
  5. Go to "Mark Attendance" to record attendance.
     - Pick the date and class.
     - Set status for each student (Present/Absent/Late).
     - Click "Save Attendance".
  6. Go to "Attendance Reports" to see summaries.
     - Filter by date range and class.
     - Click "Download CSV" to export.

AS A STUDENT:
  1. Go to http://localhost:5000
  2. Select "Student" tab.
  3. Enter your Roll No and PIN (given by your teacher).
  4. Click "Login as Student".
  5. View "My Profile" for personal details.
  6. View "My Attendance" for your attendance record.
  7. Click "Download My Attendance (CSV)" to export.


--------------------------------------------------------
7. WHERE IS THE DATA STORED?
--------------------------------------------------------
  All data is stored in:    data/school.db

  This is a SQLite database file that is created
  automatically when you first run the app.

  - students table    — all student records
  - attendance table  — all attendance entries

  BACKUP:
    Copy the "data/school.db" file to a safe location.

  RESET:
    Delete "data/school.db" and restart the app.
    A fresh, empty database will be created.

  MOVE TO ANOTHER COMPUTER:
    Copy the entire project folder (including data/).
    Your data goes with it.

  VIEW DATA DIRECTLY (optional):
    Install the "SQLite Viewer" extension in VS Code
    and open data/school.db to browse the tables.


--------------------------------------------------------
8. CSV EXPORT
--------------------------------------------------------
  Teachers can download:
    - Summary report (all students, date range, class)
    - Columns: Roll No, Name, Class, Section,
      Present, Absent, Late, Total Marked, Attendance %

  Students can download:
    - Their own attendance (date range)
    - Columns: Roll No, Name, Class, Date, Status, Remarks

  CSV files can be opened in Microsoft Excel,
  Google Sheets, or LibreOffice Calc.


--------------------------------------------------------
9. DARK MODE
--------------------------------------------------------
  A sun/moon button is fixed to the top-right corner
  of every page (including the login page).

  Click it to toggle between Light and Dark mode.
  Your preference is saved in your browser and
  remembered the next time you visit.


--------------------------------------------------------
10. TROUBLESHOOTING
--------------------------------------------------------
Problem: "python is not recognized" or "command not found"
  Fix: Python is not installed or not in PATH.
       Re-install Python and tick "Add Python to PATH".

Problem: "No module named flask"
  Fix: Run:  pip install -r requirements.txt

Problem: Browser shows "This site can't be reached"
  Fix: Make sure the app is still running (check terminal).
       Ensure you are visiting http://localhost:5000
       (not https:// — there is no SSL certificate locally).

Problem: Port 5000 already in use
  Fix: Another program is using port 5000.
       Stop that program, or edit the last line of app.py:
         port = int(os.environ.get("PORT", 5000))
       Change 5000 to another number like 8080,
       then visit http://localhost:8080 instead.

Problem: Student login says "No student found"
  Fix: The teacher must add the student first via the
       Students page, and set a PIN for them.

Problem: Dark mode preference is forgotten
  Fix: Your browser cleared local storage.
       Just click the toggle again to set your preference.


--------------------------------------------------------
11. FUTURE IMPROVEMENTS
--------------------------------------------------------
  - Multi-teacher accounts with class assignment
  - Bulk student import from Excel/CSV
  - Guardian email/SMS alerts for absent students
  - Timetable / subject-wise attendance
  - Mobile app (Android / iOS)
  - Cloud deployment for multi-school use


--------------------------------------------------------
  Built with Python, Flask, HTML, CSS, and SQLite.
  Free and open-source. No external services required.
========================================================
