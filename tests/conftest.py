import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User, Workspace


@pytest.fixture
def test_engine():
    engine = create_engine(
        "sqlite:///./test_team_task_manager.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        autocommit = dbapi_connection.autocommit
        dbapi_connection.autocommit = True

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

        dbapi_connection.autocommit = autocommit

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


@pytest.fixture
def second_user(test_db_client, test_session):
    user_data = {
        "email": "second_user@example.com",
        "username": "second_igor",
        "hashed_password": get_password_hash("hard_password"),
    }

    user = User(**user_data)
    test_session.add(user)
    test_session.commit()
    test_session.refresh(user)
    return user


@pytest.fixture
def authorize_first_user(test_db_client, first_user) -> dict[str, str]:
    login_response = test_db_client.post(
        "/api/v1/auth/login/",
        data={
            "username": first_user.username,
            "password": "hard_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }


@pytest.fixture
def authorize_second_user(test_db_client, second_user) -> dict[str, str]:
    login_response = test_db_client.post(
        "/api/v1/auth/login/",
        data={
            "username": second_user.username,
            "password": "hard_password",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {access_token}",
    }


@pytest.fixture
def first_user_workspace(
    test_db_client,
    test_session,
    authorize_first_user,
):
    workspace_data = {
        "name": "test_workspace_first_user",
        "description": "test_description",
    }
    create_workspace_response = test_db_client.post(
        "/api/v1/workspaces/",
        json=workspace_data,
        headers=authorize_first_user,
    )

    assert create_workspace_response.status_code == status.HTTP_201_CREATED

    workspace_response_data = create_workspace_response.json()
    workspace = test_session.get(Workspace, workspace_response_data["id"])
    return workspace


@pytest.fixture
def second_user_workspace(
    test_db_client,
    test_session,
    authorize_second_user,
):
    workspace_data = {
        "name": "test_workspace_second_user",
        "description": "test_description",
    }
    create_workspace_response = test_db_client.post(
        "/api/v1/workspaces/",
        json=workspace_data,
        headers=authorize_second_user,
    )

    assert create_workspace_response.status_code == status.HTTP_201_CREATED

    workspace_response_data = create_workspace_response.json()
    workspace = test_session.get(Workspace, workspace_response_data["id"])
    return workspace
