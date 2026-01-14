"""
Dependency injection for FastAPI endpoints
"""
from typing import Generator
from app.services.rag import ClauseStore

# Global clause store instance (initialized in main.py)
_clause_store: ClauseStore = None


def set_clause_store(store: ClauseStore):
    """Set the global clause store instance"""
    global _clause_store
    _clause_store = store


def get_clause_store() -> ClauseStore:
    """
    Dependency for getting ClauseStore instance
    
    Usage in endpoints:
        clause_store: ClauseStore = Depends(get_clause_store)
    """
    if _clause_store is None:
        raise RuntimeError("ClauseStore not initialized")
    return _clause_store
