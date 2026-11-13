# Student Record Management System

A Django MVT application for school student profiles, enrollments, classes, grades, attendance, and audit history. PostgreSQL is the configured primary database.

## Requirements

- Python 3.10 or newer
- PostgreSQL 14 or newer
- Visual Studio Code (recommended)

## Setup in VS Code (Windows PowerShell)

1. Open this folder in VS Code and open **Terminal → New Terminal**.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Create a PostgreSQL database and user (or use an existing local PostgreSQL account):

   ```sql
   CREATE USER srms_user WITH PASSWORD 'choose-a-strong-password';
   CREATE DATABASE student_records OWNER srms_user;
   ```

5. Copy `.env.example` to `.env` and set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` to match PostgreSQL. Django does not read `.env` automatically; set the environment variables in the terminal before running the server, or configure them in your VS Code launch profile. For a PowerShell session:

   ```powershell
   $env:SECRET_KEY = "a-long-random-secret"
   $env:DB_NAME = "student_records"
   $env:DB_USER = "srms_user"
   $env:DB_PASSWORD = "choose-a-strong-password"
   $env:DB_HOST = "127.0.0.1"
   $env:DB_PORT = "5432"
   ```

6. Create schema and an administrator:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

   Set the superuser's SRMS role to **System administrator** in Django Admin (`/admin/`), or in a Django shell:

   ```powershell
   python manage.py shell -c "from accounts.models import User; u=User.objects.get(username='YOUR_USERNAME'); u.role='ADMIN'; u.save()"
   ```

7. Start the development server and open http://127.0.0.1:8000:

   ```powershell
   python manage.py runserver
   ```

## Modules and permissions

- **System administrator:** full operational access, plus Django Admin for account and reference-data management.
- **Registrar:** student profile maintenance, enrollment processing, grade and attendance access.
- **Teacher:** class-assignment-scoped grade and attendance entry; class-linked student records.
- **Student:** personal record view when the student profile is linked to their login.

Create user accounts and set their roles in Django Admin. To enable the student portal, set the account role to **Student** and attach it to the matching student's profile using the profile's `User` field. Create academic years, semesters, courses, subjects, sections, and teacher class assignments there before processing enrollments and grades. Student IDs are generated on save; duplicate student/academic-period enrollments and duplicate class attendance are database-constrained.

The Reports screen exports student, enrollment, grade, and attendance reports as PDF, Excel (`.xlsx`), or CSV. The Students screen also provides a one-click Excel master-list download.

## Important deployment notes

Before production, set `DEBUG=False`, use a secret from a secure environment variable, configure production hosts and HTTPS, serve static/media files using an appropriate web server or object storage, and configure database backups. This initial project uses Django Admin for user and academic reference-data maintenance; deployment-specific workflows, document retention, and institutional policies should be reviewed before real student data is loaded.
