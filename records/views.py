import csv
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from accounts.decorators import roles_required
from accounts.models import User
from academics.models import (
    AcademicYear,
    ClassAssignment,
    Course,
    Enrollment,
    Grade,
    Section,
    Semester,
    Subject,
)
from attendance.models import Attendance
from .forms import GuardianFormSet, StudentForm
from .models import AuditLog, Student, StudentDocument


MANAGEMENT_LISTS = {
    "users": {
        "title": "User accounts",
        "roles": (User.Role.ADMIN,),
        "model": "accounts_user",
        "columns": ("Username", "Name", "Email", "Role", "Status"),
    },
    "academic-years": {
        "title": "Academic years",
        "roles": (User.Role.ADMIN,),
        "model": "academics_academicyear",
        "columns": ("Year", "Start date", "End date", "Current"),
    },
    "semesters": {
        "title": "Semesters",
        "roles": (User.Role.ADMIN,),
        "model": "academics_semester",
        "columns": ("Semester", "Academic year", "Start date", "End date"),
    },
    "courses": {
        "title": "Courses",
        "roles": (User.Role.ADMIN,),
        "model": "academics_course",
        "columns": ("Code", "Course", "Status"),
    },
    "subjects": {
        "title": "Subjects",
        "roles": (User.Role.ADMIN,),
        "model": "academics_subject",
        "columns": ("Code", "Subject", "Course", "Units"),
    },
    "sections": {
        "title": "Sections",
        "roles": (User.Role.ADMIN,),
        "model": "academics_section",
        "columns": ("Section", "Course", "Academic year"),
    },
    "assignments": {
        "title": "Class assignments",
        "roles": (User.Role.ADMIN,),
        "model": "academics_classassignment",
        "columns": ("Section", "Subject", "Teacher"),
    },
    "documents": {
        "title": "Student documents",
        "roles": (User.Role.ADMIN, User.Role.REGISTRAR),
        "model": "records_studentdocument",
        "columns": ("Student", "Document", "Uploaded", "Uploaded by"),
    },
    "audit-logs": {
        "title": "Audit trail",
        "roles": (User.Role.ADMIN,),
        "model": "records_auditlog",
        "columns": ("Time", "User", "Action", "Details", "IP address"),
    },
}


def _management_rows(section):
    if section == "users":
        rows = User.objects.order_by("username")
        return [
            (row.pk, [row.username, row.get_full_name() or "—", row.email or "—", row.get_role_display(), "Active" if row.is_active else "Inactive"])
            for row in rows
        ]
    if section == "academic-years":
        return [
            (row.pk, [row.name, row.start_date, row.end_date, "Yes" if row.is_current else "No"])
            for row in AcademicYear.objects.order_by("-start_date")
        ]
    if section == "semesters":
        rows = Semester.objects.select_related("academic_year")
        return [
            (row.pk, [row.name, row.academic_year.name, row.start_date, row.end_date])
            for row in rows
        ]
    if section == "courses":
        return [
            (row.pk, [row.code, row.name, "Active" if row.is_active else "Inactive"])
            for row in Course.objects.order_by("code")
        ]
    if section == "subjects":
        rows = Subject.objects.select_related("course")
        return [
            (row.pk, [row.code, row.name, row.course.name if row.course else "—", row.units])
            for row in rows
        ]
    if section == "sections":
        rows = Section.objects.select_related("course", "academic_year")
        return [
            (row.pk, [f"{row.year_level} · {row.name}", row.course.name, row.academic_year.name])
            for row in rows
        ]
    if section == "assignments":
        rows = ClassAssignment.objects.select_related("section", "subject", "teacher")
        return [
            (row.pk, [str(row.section), str(row.subject), row.teacher.get_full_name() or row.teacher.username])
            for row in rows
        ]
    if section == "documents":
        rows = StudentDocument.objects.select_related("student", "uploaded_by")
        return [
            (
                row.pk,
                [
                    f"{row.student.full_name} ({row.student.student_id})",
                    row.title,
                    row.uploaded_at,
                    row.uploaded_by.get_full_name() or row.uploaded_by.username if row.uploaded_by else "—",
                ],
            )
            for row in rows
        ]
    rows = AuditLog.objects.select_related("actor")
    return [
        (
            row.pk,
            [
                row.created_at,
                row.actor.get_full_name() or row.actor.username if row.actor else "System",
                row.action.replace("_", " ").title(),
                row.description,
                row.ip_address or "—",
            ],
        )
        for row in rows
    ]


@login_required
def management_list(request, section):
    config = MANAGEMENT_LISTS.get(section)
    if not config:
        raise Http404
    if not request.user.is_superuser and request.user.role not in config["roles"]:
        raise PermissionDenied

    is_admin = request.user.is_superuser or request.user.role == User.Role.ADMIN
    admin_model = config["model"]
    rows = [
        {
            "values": values,
            "edit_url": reverse(f"admin:{admin_model}_change", args=[pk]) if is_admin else "",
            "download_url": reverse("student_document_download", args=[pk]) if section == "documents" else "",
        }
        for pk, values in _management_rows(section)
    ]
    return render(
        request,
        "records/management_list.html",
        {
            "title": config["title"],
            "columns": config["columns"],
            "rows": rows,
            "add_url": reverse(f"admin:{admin_model}_add") if is_admin else "",
            "admin_list_url": reverse(f"admin:{admin_model}_changelist") if is_admin else "",
        },
    )


def dashboard(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if request.user.role == User.Role.STUDENT:
        student = Student.objects.filter(user=request.user).first()
        return render(request, "records/student_dashboard.html", {"student": student})
    stats = {
        "students": Student.objects.exclude(status=Student.Status.ARCHIVED).count(),
        "male": Student.objects.filter(gender=Student.Gender.MALE).exclude(status=Student.Status.ARCHIVED).count(),
        "female": Student.objects.filter(gender=Student.Gender.FEMALE).exclude(status=Student.Status.ARCHIVED).count(),
        "enrolled": Enrollment.objects.filter(status=Enrollment.Status.ENROLLED).count(),
        "inactive": Student.objects.filter(status=Student.Status.INACTIVE).count(),
        "graduated": Student.objects.filter(status=Student.Status.GRADUATED).count(),
        "teachers": User.objects.filter(role=User.Role.TEACHER, is_active=True).count(),
    }
    return render(request, "records/dashboard.html", {"stats": stats, "activities": AuditLog.objects.select_related("actor")[:8]})


@roles_required(User.Role.STUDENT)
def student_portal_section(request, section):
    section_anchors = {
        "profile": "profile",
        "enrollments": "enrollment-history",
        "grades": "academic-results",
        "attendance": "attendance-records",
        "documents": "documents",
    }
    if section not in section_anchors:
        raise Http404
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return render(
            request,
            "records/student_dashboard.html",
            {"student": None, "requested_section": section.replace("-", " ").title()},
        )
    return redirect(f"{reverse('student_detail', args=[student.pk])}#{section_anchors[section]}")


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.STUDENT)
def student_document_download(request, pk):
    document = get_object_or_404(StudentDocument.objects.select_related("student"), pk=pk)
    if request.user.role == User.Role.STUDENT and document.student.user_id != request.user.id:
        raise PermissionDenied
    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.file.name.rsplit("/", 1)[-1],
    )


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
def student_list(request):
    students = Student.objects.exclude(status=Student.Status.ARCHIVED)
    if request.user.role == User.Role.TEACHER:
        students = students.filter(enrollments__section__assignments__teacher=request.user).distinct()
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if query:
        students = students.filter(Q(student_id__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query) | Q(email__icontains=query))
    if status in Student.Status.values:
        students = students.filter(status=status)
    return render(request, "records/student_list.html", {"students": students, "query": query, "status": status})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR)
@require_http_methods(["GET", "POST"])
def student_create(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    guardians = GuardianFormSet(request.POST or None, instance=Student())
    if form.is_valid() and guardians.is_valid():
        student = form.save()
        guardians.instance = student
        guardians.save()
        AuditLog.objects.create(actor=request.user, action="STUDENT_CREATED", description=f"Created student {student}")
        messages.success(request, f"Student {student.student_id} created.")
        return redirect("student_detail", pk=student.pk)
    return render(request, "shared/form.html", {"form": form, "formset": guardians, "title": "Register student", "cancel_url": "student_list"})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER, User.Role.STUDENT)
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.prefetch_related("guardians", "documents", "enrollments__grades", "enrollments__attendance_records"), pk=pk)
    if request.user.role == User.Role.STUDENT and student.user_id != request.user.id:
        raise PermissionDenied
    if request.user.role == User.Role.TEACHER and not student.enrollments.filter(section__assignments__teacher=request.user).exists():
        raise PermissionDenied
    return render(request, "records/student_detail.html", {"student": student})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR)
@require_http_methods(["GET", "POST"])
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)
    guardians = GuardianFormSet(request.POST or None, instance=student)
    if form.is_valid() and guardians.is_valid():
        updated = form.save()
        guardians.save()
        AuditLog.objects.create(actor=request.user, action="STUDENT_UPDATED", description=f"Updated student {updated}")
        messages.success(request, "Student record updated.")
        return redirect("student_detail", pk=student.pk)
    return render(request, "shared/form.html", {"form": form, "formset": guardians, "title": "Update student", "cancel_url": "student_detail", "cancel_kwargs": {"pk": student.pk}})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR)
@require_http_methods(["POST"])
def student_archive(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.status = Student.Status.ARCHIVED
    student.save(update_fields=["status", "updated_at"])
    AuditLog.objects.create(actor=request.user, action="STUDENT_ARCHIVED", description=f"Archived student {student}")
    messages.success(request, "Student record archived.")
    return redirect("student_list")


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
def student_export(request):
    rows = Student.objects.exclude(status=Student.Status.ARCHIVED).order_by("last_name", "first_name")
    if request.user.role == User.Role.TEACHER:
        rows = rows.filter(enrollments__section__assignments__teacher=request.user).distinct()
    if request.GET.get("format") == "xlsx":
        from openpyxl import Workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Students"
        sheet.append(["Student ID", "First name", "Last name", "Gender", "Email", "Status"])
        for student in rows:
            sheet.append([student.student_id, student.first_name, student.last_name, student.get_gender_display(), student.email, student.get_status_display()])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = 'attachment; filename="student-master-list.xlsx"'
        workbook.save(response)
        return response
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="student-master-list.csv"'
    writer = csv.writer(response)
    writer.writerow(["Student ID", "First name", "Last name", "Gender", "Email", "Status"])
    for student in rows:
        writer.writerow([student.student_id, student.first_name, student.last_name, student.get_gender_display(), student.email, student.get_status_display()])
    return response


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
def report_center(request):
    return render(request, "records/reports.html")


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
def report_export(request):
    report_type = request.GET.get("report", "")
    export_format = request.GET.get("format", "xlsx")
    if export_format not in {"csv", "xlsx", "pdf"}:
        return HttpResponse("Unsupported report format.", status=400)

    if report_type == "students":
        rows = Student.objects.exclude(status=Student.Status.ARCHIVED)
        if request.user.role == User.Role.TEACHER:
            rows = rows.filter(enrollments__section__assignments__teacher=request.user).distinct()
        rows = rows.order_by("last_name", "first_name")
        headers = ["Student ID", "Student name", "Gender", "Date of birth", "Email", "Status"]
        data = ([row.student_id, row.full_name, row.get_gender_display(), row.date_of_birth, row.email, row.get_status_display()] for row in rows)
    elif report_type == "enrollments":
        rows = Enrollment.objects.select_related("student", "academic_year", "semester", "course", "section")
        if request.user.role == User.Role.TEACHER:
            rows = rows.filter(section__assignments__teacher=request.user).distinct()
        headers = ["Student ID", "Student name", "Academic year", "Semester", "Course", "Year level", "Section", "Status"]
        data = ([row.student.student_id, row.student.full_name, row.academic_year.name, row.semester.name, row.course.name, row.year_level, row.section.name if row.section else "", row.get_status_display()] for row in rows)
    elif report_type == "grades":
        rows = Grade.objects.select_related("enrollment__student", "enrollment__academic_year", "assignment__subject", "assignment__section")
        if request.user.role == User.Role.TEACHER:
            rows = rows.filter(assignment__teacher=request.user)
        headers = ["Student ID", "Student name", "Academic year", "Subject", "Section", "Grade", "Remarks"]
        data = ([row.enrollment.student.student_id, row.enrollment.student.full_name, row.enrollment.academic_year.name, row.assignment.subject.name, row.assignment.section.name, row.grade, row.remarks] for row in rows)
    elif report_type == "attendance":
        rows = Attendance.objects.select_related("enrollment__student", "assignment__subject", "recorded_by")
        if request.user.role == User.Role.TEACHER:
            rows = rows.filter(assignment__teacher=request.user)
        headers = ["Date", "Student ID", "Student name", "Subject", "Status", "Remarks"]
        data = ([row.date, row.enrollment.student.student_id, row.enrollment.student.full_name, row.assignment.subject.name if row.assignment else "", row.get_status_display(), row.remarks] for row in rows)
    else:
        return HttpResponse("Unknown report type.", status=400)

    data = list(data)
    filename = f"{report_type}-report"
    if export_format == "csv":
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(headers)
        writer.writerows(data)
        return response

    if export_format == "xlsx":
        from openpyxl import Workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = report_type.title()[:31]
        sheet.append(headers)
        for row in data:
            sheet.append([value.isoformat() if hasattr(value, "isoformat") else value for value in row])
        response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = f'attachment; filename="{filename}.xlsx"'
        workbook.save(response)
        return response

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=0.4 * inch, leftMargin=0.4 * inch)
    table_data = [headers] + [[str(value) if value is not None else "" for value in row] for row in data]
    table = Table(table_data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#142b4a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dbe1e9")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    document.build([Paragraph(f"{report_type.title()} Report", getSampleStyleSheet()["Title"]), table])
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}.pdf"'
    return response
