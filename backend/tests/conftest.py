import pytest
import uuid
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app
from app.core.security import create_access_token, get_password_hash
from app.models.user import User

# Use in-memory SQLite with StaticPool so all sessions share the exact same in-memory database
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db() -> Generator:
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def db_session(db) -> Generator:
    yield db

@pytest.fixture(scope="function")
def test_user(db) -> User:
    u = User(
        email=f"test_user_{uuid.uuid4().hex[:6]}@cashflow.local",
        hashed_password=get_password_hash("Secret123!"),
        full_name="Test Operator",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@pytest.fixture(scope="function")
def client(db) -> Generator:
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def auth_headers(user_id: str) -> dict:
    token = create_access_token(subject=user_id)
    return {"Authorization": f"Bearer {token}"}
