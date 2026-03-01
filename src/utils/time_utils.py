from datetime import datetime


def now() -> datetime:
    """Return current local datetime. Centralised for easy mocking in tests."""
    return datetime.now()
