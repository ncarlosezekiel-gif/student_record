from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.decorators import roles_required
from accounts.models import User
from records.models import AuditLog
from .forms import EnrollmentForm, GradeForm
from .models import Enrollment, Grade


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR)
def enrollment_list(request):
    return render(request, "academics/enrollments.html", {"enrollments": Enrollment.objects.select_related("student", "academic_year", "semester", "course")})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR)
@require_http_methods(["GET", "POST"])
def enrollment_create(request):
    form = EnrollmentForm(request.POST or None)
    if form.is_valid():
        try:
            enrollment = form.save()
        except IntegrityError:
            form.add_error(None, "This student already has an enrollment for that academic period.")
        else:
            AuditLog.objects.create(actor=request.user, action="ENROLLMENT_CREATED", description=f"Enrollment created for {enrollment.student}")
            messages.success(request, "Enrollment saved.")
            return redirect("enrollment_list")
    return render(request, "shared/form.html", {"form": form, "title": "New enrollment", "cancel_url": "enrollment_list"})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR)
@require_http_methods(["GET", "POST"])
def enrollment_update(request, pk):
    enrollment = get_object_or_404(Enrollment.objects.select_related("student"), pk=pk)
    form = EnrollmentForm(request.POST or None, instance=enrollment)
    if form.is_valid():
        enrollment = form.save()
        AuditLog.objects.create(actor=request.user, action="ENROLLMENT_UPDATED", description=f"Enrollment updated for {enrollment.student}")
        messages.success(request, "Enrollment updated.")
        return redirect("enrollment_list")
    return render(request, "shared/form.html", {"form": form, "title": "Update enrollment", "cancel_url": "enrollment_list"})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
def grade_list(request):
    grades = Grade.objects.select_related("enrollment__student", "assignment__subject", "updated_by")
    if request.user.role == User.Role.TEACHER:
        grades = grades.filter(assignment__teacher=request.user)
    return render(request, "academics/grades.html", {"grades": grades})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
@require_http_methods(["GET", "POST"])
def grade_create(request):
    form = GradeForm(request.POST or None)
    if request.user.role == User.Role.TEACHER:
        form.fields["assignment"].queryset = form.fields["assignment"].queryset.filter(teacher=request.user)
        form.fields["enrollment"].queryset = form.fields["enrollment"].queryset.filter(status=Enrollment.Status.ENROLLED)
    if form.is_valid():
        grade = form.save(commit=False)
        if request.user.role == User.Role.TEACHER and grade.assignment.teacher_id != request.user.id:
            form.add_error("assignment", "You can only enter grades for your assigned classes.")
        elif grade.assignment.section_id != grade.enrollment.section_id:
            form.add_error("assignment", "The class assignment must match the student's enrolled section.")
        else:
            grade.updated_by = request.user
            grade.save()
            AuditLog.objects.create(actor=request.user, action="GRADE_UPDATED", description=f"Grade {grade.grade} recorded for {grade.enrollment.student}")
            messages.success(request, "Grade saved.")
            return redirect("grade_list")
    return render(request, "shared/form.html", {"form": form, "title": "Record grade", "cancel_url": "grade_list"})


@roles_required(User.Role.ADMIN, User.Role.REGISTRAR, User.Role.TEACHER)
@require_http_methods(["GET", "POST"])
def grade_update(request, pk):
    grade = Grade.objects.select_related("assignment__teacher", "enrollment").get(pk=pk)
    if request.user.role == User.Role.TEACHER and grade.assignment.teacher_id != request.user.id:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = GradeForm(request.POST or None, instance=grade)
    if request.user.role == User.Role.TEACHER:
        form.fields["assignment"].queryset = form.fields["assignment"].queryset.filter(teacher=request.user)
        form.fields["enrollment"].queryset = form.fields["enrollment"].queryset.filter(status=Enrollment.Status.ENROLLED)
    if form.is_valid():
        updated = form.save(commit=False)
        if updated.assignment.teacher_id != request.user.id and request.user.role == User.Role.TEACHER:
            form.add_error("assignment", "You can only enter grades for your assigned classes.")
        elif updated.assignment.section_id != updated.enrollment.section_id:
            form.add_error("assignment", "The class assignment must match the student's enrolled section.")
        else:
            updated.updated_by = request.user
            updated.save()
            AuditLog.objects.create(actor=request.user, action="GRADE_UPDATED", description=f"Grade {updated.grade} updated for {updated.enrollment.student}")
            messages.success(request, "Grade updated.")
            return redirect("grade_list")
    return render(request, "shared/form.html", {"form": form, "title": "Update grade", "cancel_url": "grade_list"})
