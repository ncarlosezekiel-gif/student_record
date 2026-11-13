from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods

from records.models import AuditLog, Student
from .forms import StudentAccountCreationForm

class SRMSLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


@require_http_methods(["GET", "POST"])
def register_student_account(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = StudentAccountCreationForm(request.POST or None)
    if form.is_valid():
        email = form.cleaned_data["email"].casefold()
        try:
            with transaction.atomic():
                student = Student.objects.select_for_update().get(
                    student_id__iexact=form.cleaned_data["student_id"],
                    email__iexact=email,
                    user__isnull=True,
                )
                user_model = get_user_model()
                if user_model.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
                    form.add_error(None, StudentAccountCreationForm.MATCH_ERROR)
                else:
                    user = user_model.objects.create_user(
                        username=email,
                        email=email,
                        first_name=student.first_name,
                        last_name=student.last_name,
                        password=form.cleaned_data["password1"],
                        role=user_model.Role.STUDENT,
                    )
                    student.user = user
                    student.save(update_fields=["user", "updated_at"])
                    AuditLog.objects.create(
                        actor=user,
                        action="ACCOUNT_CREATED",
                        description=f"Student portal account created for {student.student_id}",
                        ip_address=request.META.get("REMOTE_ADDR"),
                    )
        except Student.DoesNotExist:
            form.add_error(None, StudentAccountCreationForm.MATCH_ERROR)
        except IntegrityError:
            form.add_error(None, StudentAccountCreationForm.MATCH_ERROR)
        else:
            if not form.errors:
                messages.success(request, "Your account is ready. Sign in with your email and password.")
                return redirect("login")

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    if request.method != "POST":
        return redirect("dashboard")
    logout(request)
    return redirect(reverse_lazy("login"))
