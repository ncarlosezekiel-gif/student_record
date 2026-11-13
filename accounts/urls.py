from django.urls import path
from .views import SRMSLoginView, logout_view, register_student_account

urlpatterns = [
    path("login/", SRMSLoginView.as_view(), name="login"),
    path("register/", register_student_account, name="register_student_account"),
    path("logout/", logout_view, name="logout"),
]
