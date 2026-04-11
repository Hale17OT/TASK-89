"""Sudo-mode middleware: injects active sudo action classes onto the request."""
import time


class SudoModeMiddleware:
    """
    Reads sudo token data from session, populates request.sudo_actions
    with the set of non-expired action classes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.sudo_actions = set()

        if request.user.is_authenticated:
            sudo_data = request.session.get("_sudo_tokens", {})
            now = time.time()
            active = {}
            for action_class, token_info in sudo_data.items():
                if token_info.get("expires_at", 0) > now:
                    request.sudo_actions.add(action_class)
                    active[action_class] = token_info
            # Clean expired tokens from session
            if len(active) != len(sudo_data):
                request.session["_sudo_tokens"] = active

        return self.get_response(request)
