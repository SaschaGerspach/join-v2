from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from .helpers import get_client_ip, log_audit
from .middleware import AdminAuditMiddleware
from .models import AuditLog
from .tasks import cleanup_old_audit_logs

User = get_user_model()


class AuditLogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="pass")

    def test_str(self):
        entry = AuditLog.objects.create(user=self.user, event_type="login_success")
        self.assertIn("login_success", str(entry))

    def test_ordering(self):
        AuditLog.objects.create(user=self.user, event_type="login_success", detail="first")
        AuditLog.objects.create(user=self.user, event_type="login_failed", detail="second")
        entries = list(AuditLog.objects.all())
        self.assertEqual(entries[0].detail, "second")


class LogAuditHelperTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="pass")
        self.factory = RequestFactory()

    def test_log_audit_creates_entry(self):
        request = self.factory.get("/test/")
        request.META["REMOTE_ADDR"] = "192.168.1.1"
        log_audit("login_success", user=self.user, request=request, detail="Test login")
        self.assertEqual(AuditLog.objects.count(), 1)
        entry = AuditLog.objects.first()
        self.assertEqual(entry.event_type, "login_success")
        self.assertEqual(entry.ip_address, "192.168.1.1")

    def test_log_audit_truncates_detail(self):
        log_audit("login_success", user=self.user, detail="x" * 2000)
        entry = AuditLog.objects.first()
        self.assertEqual(len(entry.detail), 1000)

    def test_log_audit_without_request(self):
        log_audit("login_success", user=self.user)
        entry = AuditLog.objects.first()
        self.assertIsNone(entry.ip_address)


class GetClientIpTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_remote_addr(self):
        request = self.factory.get("/")
        request.META["REMOTE_ADDR"] = "10.0.0.1"
        self.assertEqual(get_client_ip(request), "10.0.0.1")

    def test_x_forwarded_for(self):
        request = self.factory.get("/")
        request.META["HTTP_X_FORWARDED_FOR"] = "1.2.3.4, 5.6.7.8"
        ip = get_client_ip(request)
        self.assertIn(ip, ("1.2.3.4", "5.6.7.8"))


class AdminAuditMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(email="admin@test.com", password="pass", is_staff=True)
        self.user = User.objects.create_user(email="user@test.com", password="pass")

    def _get_response(self, request):
        from django.http import HttpResponse
        return HttpResponse(status=200)

    def test_logs_admin_write(self):
        middleware = AdminAuditMiddleware(self._get_response)
        request = self.factory.post("/admin-api/boards/")
        request.user = self.admin
        middleware(request)
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_skips_non_admin(self):
        middleware = AdminAuditMiddleware(self._get_response)
        request = self.factory.post("/admin-api/boards/")
        request.user = self.user
        middleware(request)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_skips_get_requests(self):
        middleware = AdminAuditMiddleware(self._get_response)
        request = self.factory.get("/admin-api/boards/")
        request.user = self.admin
        middleware(request)
        self.assertEqual(AuditLog.objects.count(), 0)

    def test_skips_auth_paths(self):
        middleware = AdminAuditMiddleware(self._get_response)
        request = self.factory.post("/auth/login/")
        request.user = self.admin
        middleware(request)
        self.assertEqual(AuditLog.objects.count(), 0)


class CleanupAuditLogsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@test.com", password="pass")

    def test_deletes_old_entries(self):
        old = AuditLog.objects.create(user=self.user, event_type="login_success")
        AuditLog.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=100))
        AuditLog.objects.create(user=self.user, event_type="login_success")
        deleted = cleanup_old_audit_logs()
        self.assertEqual(deleted, 1)
        self.assertEqual(AuditLog.objects.count(), 1)

    def test_keeps_recent_entries(self):
        AuditLog.objects.create(user=self.user, event_type="login_success")
        deleted = cleanup_old_audit_logs()
        self.assertEqual(deleted, 0)
        self.assertEqual(AuditLog.objects.count(), 1)
