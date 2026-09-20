import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AUTH0_DOMAIN"] = "tests.auth0.com"
os.environ["AUTH0_AUDIENCE"] = "https://api.precioinbox.test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import Base, get_db
from app.main import app
from app.security.auth0 import Auth0Principal, get_auth0_principal

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    with TestingSessionLocal() as db:
        yield db


@pytest.fixture(autouse=True)
def database():
    Base.metadata.create_all(bind=engine)
    with TestingSessionLocal() as db:
        db.add(models.Category(name="General / Otros", active=True))
        db.commit()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def authenticate_as():
    def authenticate(subject: str) -> None:
        app.dependency_overrides[get_auth0_principal] = lambda: Auth0Principal(
            subject=subject,
            claims={"sub": subject},
        )

    yield authenticate
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
