# Personalized Study Planner — AI + Admin Edition

## Included features
- Student registration/login + password recovery
- AI-assisted personalized schedule generator
- Subject type: Theory / Practical / Both
- Subject priority, interest and difficulty (1–5)
- College timing, gym, meditation, commute buffer
- Morning/evening availability and max study hours
- Study days (Mon–Sun), session length and break length
- Preferred slot, wake/sleep time, learning style, goal and target score
- Hobbies/interests and optional blocked times
- Adaptive/explainable scoring using exam urgency, pending tasks and completion history
- Search across notes, study PDFs, tasks, PYQs and uploaded PYQ PDFs
- Study PDF upload
- PYQ PDF upload
- Admin/teacher login and dashboard
- Admin monitoring of students, task progress, generated plans and recent activity
- Admin can publish notes, PDFs and PYQs for students
- Attractive responsive UI with study illustrations and glassmorphism styling
- SQLite database with automatic compatibility migrations

## Run
1. Open terminal in this project folder.
2. Install dependencies:
   `pip install -r requirements.txt`
3. Start:
   `python app.py`
4. Open:
   `http://127.0.0.1:5000`

## Demo admin login
- Email: `admin@studyplanner.local`
- Password: `Admin@123`

For real deployment, set:
- `STUDY_ADMIN_EMAIL`
- `STUDY_ADMIN_PASSWORD`

Example on Windows PowerShell:
`$env:STUDY_ADMIN_EMAIL="teacher@example.com"`
`$env:STUDY_ADMIN_PASSWORD="StrongPasswordHere"`

The default admin is created automatically on first run. Existing databases are migrated automatically for the new fields.

## AI model for viva
This version uses an explainable adaptive recommendation model rather than a cloud AI API. The focus score combines:
- Subject priority
- Student interest
- Difficulty
- Theory/practical importance
- Exam urgency
- Pending task urgency
- Previous task completion pattern
- Preferred study slot
- Target score

This makes the schedule student-specific and keeps the project fully offline.


ADMIN SUBJECT CONTROL + PREMIUM PRESENTATION
--------------------------------------------
- Admin can add new subjects from Admin > Manage Subjects.
- Admin can remove/restore subjects without deleting existing academic material.
- Removed subjects are hidden from new Notes, PDF, PYQ, Task and AI Plan selections.
- Existing notes, PDFs, PYQs, tasks and generated plans are preserved.
- Dashboard includes a premium project-speciality section highlighting the explainable personalization engine.
- Admin dashboard includes the same project speciality overview and subject management.
- Existing core features and scheduling logic are retained.
