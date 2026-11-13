from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("management/<slug:section>/", views.management_list, name="management_list"),
    path("my/<slug:section>/", views.student_portal_section, name="student_portal_section"),
    path("documents/<int:pk>/download/", views.student_document_download, name="student_document_download"),
    path("students/", views.student_list, name="student_list"),
    path("students/new/", views.student_create, name="student_create"),
    path("students/export/", views.student_export, name="student_export"),
    path("reports/", views.report_center, name="report_center"),
    path("reports/export/", views.report_export, name="report_export"),
    path("students/<int:pk>/", views.student_detail, name="student_detail"),
    path("students/<int:pk>/edit/", views.student_update, name="student_update"),
    path("students/<int:pk>/archive/", views.student_archive, name="student_archive"),
]
