from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from records.models import Student


class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date <= self.start_date:
            raise ValidationError({"end_date": "End date must be after start date."})


class Semester(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="semesters")
    name = models.CharField(max_length=40)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=("academic_year", "name"), name="unique_semester_per_year")]
        ordering = ["academic_year", "start_date"]

    def __str__(self):
        return f"{self.academic_year} - {self.name}"


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    units = models.DecimalField(max_digits=4, decimal_places=1, default=3)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="subjects", null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Section(models.Model):
    name = models.CharField(max_length=80)
    year_level = models.CharField(max_length=40)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="sections")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="sections")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("name", "year_level", "academic_year"), name="unique_section_year_level")]

    def __str__(self):
        return f"{self.year_level} - {self.name}"


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ENROLLED = "ENROLLED", "Enrolled"
        REJECTED = "REJECTED", "Rejected"
        WITHDRAWN = "WITHDRAWN", "Withdrawn"

    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="enrollments")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT, related_name="enrollments")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="enrollments")
    section = models.ForeignKey(Section, on_delete=models.PROTECT, related_name="enrollments", null=True, blank=True)
    year_level = models.CharField(max_length=40)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-enrolled_at"]
        constraints = [models.UniqueConstraint(fields=("student", "academic_year", "semester"), name="unique_student_period_enrollment")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.semester_id and self.academic_year_id and self.semester.academic_year_id != self.academic_year_id:
            raise ValidationError({"semester": "The selected semester must belong to the selected academic year."})
        if self.section_id and self.academic_year_id and self.section.academic_year_id != self.academic_year_id:
            raise ValidationError({"section": "The section must belong to the selected academic year."})
        if self.section_id and self.course_id and self.section.course_id != self.course_id:
            raise ValidationError({"section": "The section must belong to the selected course."})

    def __str__(self):
        return f"{self.student} - {self.academic_year} ({self.semester})"

    @property
    def weighted_average(self):
        grades = list(self.grades.select_related("assignment__subject").all())
        units = sum((grade.assignment.subject.units for grade in grades), start=0)
        if not units:
            return None
        weighted_total = sum(
            (grade.grade * grade.assignment.subject.units for grade in grades),
            start=0,
        )
        return (weighted_total / units).quantize(Decimal("0.01"))

    @property
    def attendance_percentage(self):
        records = self.attendance_records.exclude(status="EXCUSED")
        total = records.count()
        if not total:
            return None
        attended = records.filter(status__in=("PRESENT", "LATE")).count()
        return round(attended * 100 / total, 2)


class ClassAssignment(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="assignments")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="assignments")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, limit_choices_to={"role": "TEACHER"}, related_name="class_assignments")

    class Meta:
        constraints = [models.UniqueConstraint(fields=("section", "subject"), name="unique_subject_per_section")]

    def __str__(self):
        return f"{self.section} - {self.subject}"


class Grade(models.Model):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="grades")
    assignment = models.ForeignKey(ClassAssignment, on_delete=models.PROTECT, related_name="grades")
    grade = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(100)])
    remarks = models.CharField(max_length=200, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("enrollment", "assignment"), name="unique_grade_per_enrollment_subject")]

    def __str__(self):
        return f"{self.enrollment.student} - {self.assignment.subject}: {self.grade}"
