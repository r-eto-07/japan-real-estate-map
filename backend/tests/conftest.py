"""テスト用 PostgreSQL（別 DB）のセットアップ。

DATABASE_URL の DB 名に "_test" を付けた別データベースを使用し、
開発用 DB を pytest で破壊しない（§46）。
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

import app.db.models  # noqa: F401  -- Base.metadata へモデル登録
from app import config
from app.db.base import Base

_BASE_URL = make_url(config.require_database_url())
_TEST_URL = _BASE_URL.set(database=f"{_BASE_URL.database}_test")
_ADMIN_URL = _BASE_URL.set(database="postgres")

_TABLES = (
    "real_estate_transactions",
    "land_price_points",
    "rent_statistics",
    "municipalities",
)


@pytest.fixture(scope="session")
def test_engine():
    admin = create_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": _TEST_URL.database},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{_TEST_URL.database}"'))
    admin.dispose()

    engine = create_engine(_TEST_URL)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_factory(test_engine) -> sessionmaker[Session]:
    return sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _clean_tables(test_engine) -> Iterator[None]:
    with test_engine.begin() as conn:
        conn.execute(
            text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE")
        )
    yield


@pytest.fixture
def db(test_session_factory) -> Iterator[Session]:
    session = test_session_factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture
def api_client(test_session_factory) -> Iterator[TestClient]:
    from app.dependencies import get_db
    from app.main import app

    def _override_get_db() -> Iterator[Session]:
        session = test_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
