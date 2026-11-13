from django.contrib import admin
from django.db import connection
from django.http import JsonResponse
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check, name="health_check"),
    path("accounts/", include("accounts.urls")),
    path("", include("records.urls")),
    path("academics/", include("academics.urls")),
    path("attendance/", include("attendance.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
