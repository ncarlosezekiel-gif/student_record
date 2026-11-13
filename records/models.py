import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Student(models.Model):
    class Gender(models.TextChoices):
        FEMALE = "F", "Female"
        MALE = "M", "Male"
        OTHER = "X", "Other"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        GRADUATED = "GRADUATED", "Graduated"
        ARCHIVED = "ARCHIVED", "Archived"

    student_id = models.CharField(max_length=20, unique=True, editable=False)
    first_name = models.CharField(max_length=80)
    middle_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80)
    suffix = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=Gender.choices)
    civil_status = models.CharField(max_length=30, blank=True)
    address = models.TextField()
    contact_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    profile_picture = models.ImageField(upload_to="students/", blank=True)
    emergency_contact_name = models.CharField(max_length=160, blank=True)
    emergency_contact_number = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="student_profile")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def save(self, *args, **kwargs):
        if not self.student_id:
            self.student_id = f"SR{timezone.now():%y%m}-" + uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    @property
    def age(self):
        today = timezone.localdate()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    @property
    def full_name(self):
        return " ".join(part for part in (self.first_name, self.middle_name, self.last_name, self.suffix) if part)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


class Guardian(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="guardians")
    name = models.CharField(max_length=160)
    relationship = models.CharField(max_length=60)
    contact_number = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.relationship})"


class StudentDocument(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=160)
    file = models.FileField(upload_to="student_documents/")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=80)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action}: {self.description[:80]}"
