from django.contrib import admin
from .models import AuditLog, Guardian, Student, StudentDocument


class GuardianInline(admin.TabularInline):
    model = Guardian
    extra = 0


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "last_name", "first_name", "gender", "status")
    list_filter = ("status", "gender")
    search_fields = ("student_id", "first_name", "last_name", "email")
    inlines = (GuardianInline,)


admin.site.register((StudentDocument, AuditLog))
