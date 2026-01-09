"""
Carbon Room Core Module
=======================
Production-grade data infrastructure for creator IP registry.
"""

from .config import settings
from .ip_registry import IPRegistry

__all__ = ["settings", "IPRegistry"]

# Database imports (lazy to avoid circular dependencies)
def get_db():
    from .database import get_db as _get_db
    return _get_db()

def init_db():
    from .database import init_db as _init_db
    return _init_db()
