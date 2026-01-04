#!/usr/bin/env python3
"""Initialize database tables"""
import sys
sys.path.insert(0, '/app')

from app.core.database import Base, engine
from app.models.signal import Signal  # Import models to register them

def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
