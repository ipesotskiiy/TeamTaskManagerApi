import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite:///./test_team_task_manager.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def test_session(test_engine):
    SessionLocal = sessionmaker(bind=test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def test_db_client(test_session):

    def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def first_user(test_db_client, test_session):
    user_data = {
        "email": "first_user@example.com",
        "username": "igor",
        "hashed_password": get_password_hash("hard_password"),
    }

    user = User(**user_data)
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user

