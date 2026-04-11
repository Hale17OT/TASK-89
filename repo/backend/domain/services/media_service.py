"""
Pure-Python media domain service.
No Django imports -- only stdlib.
"""

VALID_TRANSITIONS = {
    "open": {"investigating"},
    "investigating": {"resolved", "dismissed"},
    "resolved": set(),
    "dismissed": set(),
}


def validate_infringement_transition(old_status: str, new_status: str) -> bool:
    """
    Return True if the transition from *old_status* to *new_status* is
    allowed, False otherwise.
    """
    allowed = VALID_TRANSITIONS.get(old_status, set())
    return new_status in allowed
