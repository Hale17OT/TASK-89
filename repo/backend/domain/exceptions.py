"""Domain-level exceptions. No Django dependencies."""


class DomainError(Exception):
    """Base exception for domain errors."""
    pass


class ValidationError(DomainError):
    """Domain validation error."""
    pass


class AuthorizationError(DomainError):
    """Authorization check failed."""
    pass


class ConflictError(DomainError):
    """Conflicting state (e.g., duplicate, already revoked)."""
    pass


class NotFoundError(DomainError):
    """Requested resource not found."""
    pass


class FinancialDeleteAttemptError(DomainError):
    """Attempted to delete a financial record."""
    pass
