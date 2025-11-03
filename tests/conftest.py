import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import create_app
from app.db.models import Base, Legislator

@pytest.fixture(scope="session")
def test_db_url(tmp_path_factory):
    dbfile = tmp_path_factory.mktemp("db") / "test.db"
    return f"sqlite:///{dbfile}"

@pytest.fixture(scope="session", autouse=True)
def set_test_env(test_db_url, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", test_db_url)
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    monkeypatch.setenv("LOG_FORMAT", "plain")

@pytest.fixture()
def app(test_db_url):
    application = create_app()
    engine = create_engine(test_db_url)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return application

@pytest.fixture()
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

@pytest.fixture()
def db_session(test_db_url):
    engine = create_engine(test_db_url)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        yield s

@pytest.fixture()
def seed_legislators(db_session):
    rows = [
        Legislator(govtrack_id=1, first_name="Ada", last_name="Lovelace", type="rep", state="CA",
                   district=1, party="Democrat", gender="F"),
        Legislator(govtrack_id=2, first_name="Grace", last_name="Hopper", type="sen", state="NY",
                   district=None, party="Republican", gender="F"),
        Legislator(govtrack_id=3, first_name="Alan", last_name="Turing", type="rep", state="NY",
                   district=2, party="Independent", gender="M"),
    ]
    db_session.add_all(rows)
    db_session.commit()
    yield
