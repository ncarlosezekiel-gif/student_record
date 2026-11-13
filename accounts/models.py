from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "System administrator"
        REGISTRAR = "REGISTRAR", "Registrar"
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=12, choices=Role.choices, default=Role.REGISTRAR)
    phone = models.CharField(max_length=30, blank=True)

    def save(self, *args, **kwargs):
        self.is_staff = self.is_superuser or self.role == self.Role.ADMIN
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        if self.is_active and self.role == self.Role.ADMIN:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_active and self.role == self.Role.ADMIN:
            return True
        return super().has_module_perms(app_label)

    def __str__(self):
        return self.get_full_name() or self.username
