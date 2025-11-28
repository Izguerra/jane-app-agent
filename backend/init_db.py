#!/usr/bin/env python3
"""Initialize the database with tables"""

from backend.database import init_db

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
