from django.urls import path
from .views import SRMSLoginView, logout_view

urlpatterns = [
    path("login/", SRMSLoginView.as_view(), name="login"),
    path("logout/", logout_view, name="logout"),
]
