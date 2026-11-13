from django.urls import path
from . import views

urlpatterns = [
    path("classes/", views.class_list, name="class_list"),
    path("enrollments/", views.enrollment_list, name="enrollment_list"),
    path("enrollments/new/", views.enrollment_create, name="enrollment_create"),
    path("enrollments/<int:pk>/edit/", views.enrollment_update, name="enrollment_update"),
    path("grades/", views.grade_list, name="grade_list"),
    path("grades/new/", views.grade_create, name="grade_create"),
    path("grades/<int:pk>/edit/", views.grade_update, name="grade_update"),
]
