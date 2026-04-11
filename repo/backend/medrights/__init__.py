def _get_celery_app():
    """Lazy accessor -- avoids eager celery import in non-worker contexts."""
    from .celery import app
    return app


def __getattr__(name: str):
    """Module-level __getattr__ provides lazy access to celery_app."""
    if name == "celery_app":
        return _get_celery_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ("celery_app",)
