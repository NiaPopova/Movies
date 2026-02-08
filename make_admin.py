from app import app
from model import db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "admin"
    email = "admin@site.com"
    password = "admin123"

    u = User.query.filter_by(username=username).first()
    if not u:
        u = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method="pbkdf2:sha256", salt_length=16),
            role="admin",
        )
        db.session.add(u)
    else:
        u.role = "admin"

    db.session.commit()
    print("Admin ready:", u.username, u.role)
