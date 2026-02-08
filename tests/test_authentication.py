from werkzeug.security import generate_password_hash
from model import db, User


def test_register_and_login(client):
    resp = client.post(
        "/register",
        data={"username": "u1", "email": "u1@test.com", "password": "pass123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    resp = client.post(
        "/login",
        data={"username": "u1", "password": "pass123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200


def test_admin_role_saved(app):
    with app.app_context():
        u = User(
            username="admin",
            email="admin@test.com",
            password=generate_password_hash("admin123", method="pbkdf2:sha256", salt_length=16),
            role="admin",
        )
        db.session.add(u)
        db.session.commit()
        assert u.role == "admin"
