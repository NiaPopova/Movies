from model import db, User, Movie, Collection


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password}, follow_redirects=True)


def test_default_collections_created(client, app):
    client.post(
        "/register",
        data={"username": "u1", "email": "u1@test.com", "password": "pass123"},
        follow_redirects=True,
    )
    login(client, "u1", "pass123")

    with app.app_context():
        u = User.query.filter_by(username="u1").first()
        cols = Collection.query.filter_by(user_id=u.id, is_default=True).all()
        names = sorted([c.name for c in cols])
        assert names == ["To watch", "Watching", "Watched"]


def test_default_collections_are_exclusive(client, app):
    client.post(
        "/register",
        data={"username": "u1", "email": "u1@test.com", "password": "pass123"},
        follow_redirects=True,
    )
    login(client, "u1", "pass123")

    with app.app_context():
        m = Movie(title="Inception", year=2010)
        db.session.add(m)
        db.session.commit()

        u = User.query.filter_by(username="u1").first()
        to_watch = Collection.query.filter_by(user_id=u.id, name="To watch", is_default=True).first()
        watched = Collection.query.filter_by(user_id=u.id, name="Watched", is_default=True).first()

        movie_id = m.id
        to_watch_id = to_watch.id
        watched_id = watched.id

    client.post(f"/collections/{to_watch_id}/add/{movie_id}", follow_redirects=True)
    client.post(f"/collections/{watched_id}/add/{movie_id}", follow_redirects=True)

    with app.app_context():
        to_watch = Collection.query.get(to_watch_id)
        watched = Collection.query.get(watched_id)
        assert all(mm.id != movie_id for mm in to_watch.movies)
        assert any(mm.id == movie_id for mm in watched.movies)
