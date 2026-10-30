
import hmac
import os

from django.db import connection
from django.http import JsonResponse


def database_health(request):
    if request.method != "GET":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    expected_token = os.environ.get("DIAGNOSTICS_TOKEN", "")
    provided_token = request.headers.get("X-Diagnostics-Token", "")

    if not expected_token or not hmac.compare_digest(
        expected_token, provided_token
    ):
        return JsonResponse({"detail": "Not found"}, status=404)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    current_database(),
                    current_user,
                    EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                          AND table_name = 'django_migrations'
                    )
                """
            )
            database_name, database_user, migrations_exists = cursor.fetchone()

        return JsonResponse({
            "status": "ok",
            "database_engine": connection.vendor,
            "database_name": database_name,
            "database_user": database_user,
            "django_migrations_exists": migrations_exists,
        })

    except Exception:
        return JsonResponse(
            {"status": "error", "detail": "Database connection failed"},
            status=503,
        )
