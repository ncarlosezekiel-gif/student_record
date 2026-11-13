from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("students/", views.student_list, name="student_list"),
    path("students/new/", views.student_create, name="student_create"),
    path("students/export/", views.student_export, name="student_export"),
    path("reports/", views.report_center, name="report_center"),
    path("reports/export/", views.report_export, name="report_export"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("students/<int:pk>/edit/", views.student_update, name="student_update"),
    path("students/<int:pk>/archive/", views.student_archive, name="student_archive"),
]
