"""Flask REST API for Archaeological Classifier System."""


def __getattr__(name):
    """Lazy import to avoid RuntimeWarning when running as __main__."""
    if name == "create_app":
        from acs.api.app import create_app
        return create_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["create_app"]
