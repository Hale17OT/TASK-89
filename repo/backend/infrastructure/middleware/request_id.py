"""Generates a unique request ID for every request for log correlation."""
import uuid


class RequestIDMiddleware:
    """
    Assign a UUID to every incoming request.
    Stored on request.request_id and returned in X-Request-ID header.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id

        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response
