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

## Deploy on Render

The included [render.yaml](./render.yaml) creates a free Render web service. Its `DATABASE_URL` is intentionally a required secret: create a PostgreSQL database in Render and provide that database's **internal** connection URL when prompted or set it in the web service environment. Do not commit the URL, password, or a production `.env` file.

1. Push this project, including `render.yaml`, to a GitHub repository that you can access.
2. In Render, choose **New → Blueprint**, connect the GitHub repository, and deploy. The Blueprint provisions a PostgreSQL database and connects its URL to the web service automatically. If you already created a database, edit the `DATABASE_URL` mapping in `render.yaml` to reference that Render database's name before deploying.
3. Keep the web service and database in the same Render region. The build script installs dependencies, collects static assets, and applies Django migrations; the database must be available during the build.
5. In the deployed service's Shell, create an administrator with `python manage.py createsuperuser`. Visit `/admin/` to add accounts and academic reference data. Check `/health/` for the database-backed health status.

The blueprint sets `DEBUG=False`, generates a `SECRET_KEY`, configures HTTPS/CSRF trusted origins, serves static files through WhiteNoise, and starts the app with Gunicorn. The web service is configured on Render's free plan; PostgreSQL plan availability and retention depend on Render's current offering. Free instance storage is ephemeral, so uploaded profile images and documents will not be durable across redeploys; configure persistent object storage before relying on uploaded files.

**GitHub prerequisite:** the GitHub account used to push must have write access to the repository. The local project previously could not be pushed because GitHub authenticated as an account without repository access; Render cannot deploy until the commit and Render configuration are pushed.

## Modules and permissions

- **System administrator:** full operational access, plus Django Admin for account and reference-data management.
- **Registrar:** student profile maintenance, enrollment processing, grade and attendance access.
- **Teacher:** class-assignment-scoped grade and attendance entry; class-linked student records.
- **Student:** personal record view when the student profile is linked to their login.

Create administrator, registrar, and teacher accounts in Django Admin and assign their roles there. Anyone can use **Create an account** on the sign-in page with an email and password; new accounts receive only the student role. A registrar must link the account to a student profile in Django Admin before it can view any student records. Create academic years, semesters, courses, subjects, sections, and teacher class assignments in Django Admin before processing enrollments and grades. Student IDs are generated on save; duplicate student/academic-period enrollments and duplicate class attendance are database-constrained.

The authenticated sidebar shows navigation based on the account role: students see profile, enrollment, grade, attendance, and document links; teachers see their assigned classes and students, grades, attendance, and reports; registrars see student, enrollment, class, academic, document, and reporting pages; administrators also get dedicated list pages for user accounts, academic years, semesters, courses, subjects, sections, assignments, documents, and audit history. Administrator list actions link to the existing Django Admin create/edit forms. Student document downloads are restricted to their owner or authorized staff.

The Reports screen exports student, enrollment, grade, and attendance reports as PDF, Excel (`.xlsx`), or CSV. The Students screen also provides a one-click Excel master-list download.

## Important deployment notes

Before production, set `DEBUG=False`, use a secret from a secure environment variable, configure production hosts and HTTPS, serve static/media files using an appropriate web server or object storage, and configure database backups. This initial project uses Django Admin for user and academic reference-data maintenance; deployment-specific workflows, document retention, and institutional policies should be reviewed before real student data is loaded.
