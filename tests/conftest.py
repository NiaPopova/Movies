import pytest
from app import app as flask_app
from model import db


@pytest.fixture()
def app():
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SECRET_KEY="test",
        LOGIN_DISABLED=False,
    )

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
