from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import AuditLog


def record_auth_event(action):
    def receiver(sender, request, user, **kwargs):
        AuditLog.objects.create(
            actor=user,
            action=action,
            description=f"{user.get_username()} {action.lower()}",
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
        )

    return receiver


user_logged_in.connect(record_auth_event("LOGIN"), dispatch_uid="srms_login_audit")
user_logged_out.connect(record_auth_event("LOGOUT"), dispatch_uid="srms_logout_audit")
