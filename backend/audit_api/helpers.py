from .models import AuditLog


def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_audit(event_type, *, user=None, request=None, detail=""):
    AuditLog.objects.create(
        user=user,
        event_type=event_type,
        detail=detail,
        ip_address=get_client_ip(request) if request else None,
    )
