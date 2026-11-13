from django.conf import settings
from django.db import models
from django.db.models import Q
from academics.models import Enrollment, ClassAssignment


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"
        EXCUSED = "EXCUSED", "Excused"

    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="attendance_records")
    assignment = models.ForeignKey(ClassAssignment, on_delete=models.CASCADE, related_name="attendance_records", null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=8, choices=Status.choices)
    remarks = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-date", "enrollment__student__last_name"]
        constraints = [
            models.UniqueConstraint(fields=("enrollment", "assignment", "date"), condition=Q(assignment__isnull=False), name="unique_class_attendance_per_day"),
            models.UniqueConstraint(fields=("enrollment", "date"), condition=Q(assignment__isnull=True), name="unique_general_attendance_per_day"),
        ]

    def __str__(self):
        return f"{self.enrollment.student} - {self.date}: {self.status}"
