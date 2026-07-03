from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session

from database.models import get_session_factory, init_db


@contextmanager
def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def setup_database():
    init_db()
