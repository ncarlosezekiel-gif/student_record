from django.contrib import admin
from .models import AcademicYear, ClassAssignment, Course, Enrollment, Grade, Section, Semester, Subject

admin.site.register((AcademicYear, Semester, Course, Subject, Section, Enrollment, ClassAssignment, Grade))
