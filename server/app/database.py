"""
Database configuration (placeholder)
Since you're using Supabase, this is a minimal placeholder
"""
from typing import Generator

class Database:
    """Placeholder database class"""
    pass

def get_db() -> Generator[Database, None, None]:
    """Database dependency (placeholder for Supabase)"""
    db = Database()
    try:
        yield db
    finally:
        pass