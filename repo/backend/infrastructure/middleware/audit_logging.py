"""Audit logging middleware: captures all auditable requests.

Writes an audit entry for ANY HTTP method (including GET) when the
view has populated ``request._audit_context``.  This ensures
read-access events (patient views, consent lookups, break-glass
reads, search queries) are logged alongside state-changing operations.
"""
import logging

logger = logging.getLogger("medrights.audit")


class AuditLoggingMiddleware:
    """
    After response processing, checks if the view annotated
    request._audit_context and creates an audit log entry.
    Works for all HTTP methods -- views opt in by setting the context.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._audit_context = {}

        response = self.get_response(request)

        if (
            hasattr(request, "_audit_context")
            and request._audit_context.get("event_type")
        ):
            try:
                from apps.audit.service import create_audit_entry

                ctx = request._audit_context
                create_audit_entry(
                    event_type=ctx["event_type"],
                    user=request.user if request.user.is_authenticated else None,
                    username_snapshot=getattr(request.user, "username", "anonymous"),
                    client_ip=getattr(request, "client_ip", ""),
                    workstation_id=getattr(request, "workstation_id", ""),
                    target_model=ctx.get("target_model", ""),
                    target_id=str(ctx.get("target_id", "")),
                    target_repr=ctx.get("target_repr", ""),
                    field_changes=ctx.get("field_changes", {}),
                    extra_data=ctx.get("extra_data", {}),
                )
            except Exception:
                logger.exception("Failed to create audit entry")

        return response
