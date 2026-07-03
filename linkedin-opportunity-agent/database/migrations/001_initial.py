"""Initial database migration — tables created via SQLAlchemy models."""

from database.models import init_db

if __name__ == "__main__":
    init_db()
    print("Database tables created.")
