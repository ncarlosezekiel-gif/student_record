from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import roles_required
from accounts.models import User
from records.models import AuditLog
from academics.models import Enrollment
from .forms import AttendanceForm
from .models import Attendance


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
def attendance_list(request):
    rows = Attendance.objects.select_related("enrollment__student", "assignment__subject", "recorded_by")
    if request.user.role == User.Role.TEACHER:
        rows = rows.filter(assignment__teacher=request.user)
    return render(request, "attendance/list.html", {"attendance_records": rows})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
@require_http_methods(["GET", "POST"])
def attendance_create(request):
    form = AttendanceForm(request.POST or None)
    if request.user.role == User.Role.TEACHER:
        form.fields["assignment"].queryset = form.fields["assignment"].queryset.filter(teacher=request.user)
        form.fields["enrollment"].queryset = form.fields["enrollment"].queryset.filter(status=Enrollment.Status.ENROLLED)
    if form.is_valid():
        attendance = form.save(commit=False)
        if request.user.role == User.Role.TEACHER and (not attendance.assignment or attendance.assignment.teacher_id != request.user.id):
            form.add_error("assignment", "Select one of your assigned classes.")
        elif attendance.assignment and attendance.assignment.section_id != attendance.enrollment.section_id:
            form.add_error("assignment", "The class assignment must match the student's enrolled section.")
        else:
            attendance.recorded_by = request.user
            try:
                attendance.save()
            except IntegrityError:
                form.add_error(None, "Attendance has already been recorded for this student, class, and date.")
            else:
                AuditLog.objects.create(actor=request.user, action="ATTENDANCE_RECORDED", description=f"{attendance.status} for {attendance.enrollment.student} on {attendance.date}")
                messages.success(request, "Attendance saved.")
                return redirect("attendance_list")
    return render(request, "shared/form.html", {"form": form, "title": "Record attendance", "cancel_url": "attendance_list"})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
@require_http_methods(["GET", "POST"])
def attendance_update(request, pk):
    record = get_object_or_404(Attendance.objects.select_related("assignment"), pk=pk)
    if request.user.role == User.Role.TEACHER and (not record.assignment or record.assignment.teacher_id != request.user.id):
        raise PermissionDenied
    form = AttendanceForm(request.POST or None, instance=record)
    if request.user.role == User.Role.TEACHER:
        form.fields["assignment"].queryset = form.fields["assignment"].queryset.filter(teacher=request.user)
        form.fields["enrollment"].queryset = form.fields["enrollment"].queryset.filter(status=Enrollment.Status.ENROLLED)
    if form.is_valid():
        attendance = form.save(commit=False)
        if request.user.role == User.Role.TEACHER and (not attendance.assignment or attendance.assignment.teacher_id != request.user.id):
                form.add_error("assignment", "Select one of your assigned classes.")
        elif attendance.assignment and attendance.assignment.section_id != attendance.enrollment.section_id:
                form.add_error("assignment", "The class assignment must match the student's enrolled section.")
        else:
                attendance.recorded_by = request.user
                try:
                    attendance.save()
                except IntegrityError:
                    form.add_error(None, "Attendance has already been recorded for this student, class, and date.")
                else:
                    AuditLog.objects.create(actor=request.user, action="ATTENDANCE_UPDATED", description=f"Attendance updated for {attendance.enrollment.student} on {attendance.date}")
                    messages.success(request, "Attendance updated.")
                    return redirect("attendance_list")
    return render(request, "shared/form.html", {"form": form, "title": "Update attendance", "cancel_url": "attendance_list"})
