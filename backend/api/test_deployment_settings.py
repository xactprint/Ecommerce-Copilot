import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase


SETTINGS_READER = """
import json
import config.settings as settings

print(json.dumps({
    "allowed_hosts": settings.ALLOWED_HOSTS,
    "cors_allowed_origins": settings.CORS_ALLOWED_ORIGINS,
    "csrf_trusted_origins": settings.CSRF_TRUSTED_ORIGINS,
    "database_engine": settings.DATABASES["default"]["ENGINE"],
    "vercel_url": settings.VERCEL_URL,
}))
"""


class DeploymentSettingsTests(SimpleTestCase):
    backend_dir = Path(__file__).resolve().parents[1]

    def run_settings(self, **overrides):
        env = os.environ.copy()
        env.update(
            {
                "DJANGO_DEBUG": "false",
                "DJANGO_SECRET_KEY": "test-secret-key",
                "DJANGO_ALLOWED_HOSTS": "",
                "DJANGO_CORS_ALLOWED_ORIGINS": "https://frontend.example.com",
                "DJANGO_CSRF_TRUSTED_ORIGINS": "",
                "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
                "VERCEL_URL": "",
            }
        )
        env.update(overrides)

        return subprocess.run(
            [sys.executable, "-c", SETTINGS_READER],
            cwd=self.backend_dir,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def read_settings(self, **overrides):
        result = self.run_settings(**overrides)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_vercel_url_is_applied_before_the_allowed_hosts_guard(self):
        settings = self.read_settings(VERCEL_URL="preview-abc.vercel.app")

        self.assertEqual(settings["allowed_hosts"], ["preview-abc.vercel.app"])

    def test_preview_can_start_with_vercel_url_only(self):
        result = self.run_settings(VERCEL_URL="preview-abc.vercel.app")

        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_production_without_any_allowed_host_fails_securely(self):
        result = self.run_settings(VERCEL_URL="")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_ALLOWED_HOSTS ou VERCEL_URL", result.stderr)

    def test_custom_domains_are_added_explicitly(self):
        settings = self.read_settings(
            DJANGO_ALLOWED_HOSTS="example.com,www.example.com",
            VERCEL_URL="preview-abc.vercel.app",
        )

        self.assertEqual(
            settings["allowed_hosts"],
            ["example.com", "www.example.com", "preview-abc.vercel.app"],
        )
        self.assertNotIn("*", settings["allowed_hosts"])

    def test_vercel_url_is_normalized_for_hosts_and_csrf(self):
        settings = self.read_settings(
            VERCEL_URL="https://Preview-Abc.Vercel.App/some/path",
        )

        self.assertEqual(settings["vercel_url"], "preview-abc.vercel.app")
        self.assertEqual(settings["allowed_hosts"], ["preview-abc.vercel.app"])
        self.assertEqual(
            settings["csrf_trusted_origins"],
            ["https://preview-abc.vercel.app"],
        )

    def test_preview_is_not_implicitly_added_to_cors(self):
        settings = self.read_settings(VERCEL_URL="preview-abc.vercel.app")

        self.assertEqual(
            settings["cors_allowed_origins"],
            ["https://frontend.example.com"],
        )

    def test_sqlite_is_refused_when_debug_is_false(self):
        result = self.run_settings(
            VERCEL_URL="preview-abc.vercel.app",
            DATABASE_URL="sqlite:///:memory:",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PostgreSQL", result.stderr)
