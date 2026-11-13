from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy


class SRMSLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


def logout_view(request):
    if request.method != "POST":
        return redirect("dashboard")
    logout(request)
    return redirect(reverse_lazy("login"))
