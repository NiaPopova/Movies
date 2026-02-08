from __future__ import annotations

from app import app
from model import db, Movie, Genre, Director, User, Review, Favorite, Collection
from werkzeug.security import generate_password_hash


def get_or_create_genre(name: str) -> Genre:
    g = Genre.query.filter_by(name=name).first()
    if not g:
        g = Genre(name=name)
        db.session.add(g)
    return g


def get_or_create_director(name: str) -> Director:
    d = Director.query.filter_by(name=name).first()
    if not d:
        d = Director(name=name)
        db.session.add(d)
    return d


def get_or_create_movie(title: str, year: int | None = None) -> Movie:
    m = Movie.query.filter_by(title=title, year=year).first()
    if not m:
        m = Movie(title=title, year=year)
        db.session.add(m)
    return m


def get_or_create_user(username: str, email: str, password: str, role: str = "user") -> User:
    u = User.query.filter_by(username=username).first()
    if not u:
        u = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method="pbkdf2:sha256", salt_length=16),
            role=role,
        )
        db.session.add(u)
    return u


def ensure_default_collections(user_id: int) -> None:
    defaults = ["To watch", "Watching", "Watched"]
    existing = Collection.query.filter_by(user_id=user_id, is_default=True).all()
    existing_names = {c.name for c in existing}

    created = False
    for name in defaults:
        if name not in existing_names:
            db.session.add(Collection(user_id=user_id, name=name, is_default=True))
            created = True

    if created:
        db.session.commit()


def get_default_collection(user_id: int, name: str) -> Collection:
    c = Collection.query.filter_by(user_id=user_id, name=name, is_default=True).first()
    if not c:
        ensure_default_collections(user_id)
        c = Collection.query.filter_by(user_id=user_id, name=name, is_default=True).first()
    return c


with app.app_context():

    admin = get_or_create_user("admin", "admin@site.com", "admin123", role="admin")
    u1 = get_or_create_user("niya", "niya@test.com", "pass123", role="user")
    u2 = get_or_create_user("maria", "maria@test.com", "pass123", role="user")

    db.session.commit()

    ensure_default_collections(admin.id)
    ensure_default_collections(u1.id)
    ensure_default_collections(u2.id)

    movies_data = [
        {
            "title": "Inception",
            "year": 2010,
            "director": "Christopher Nolan",
            "genres": ["Sci-Fi", "Action", "Thriller"],
            "description": "A mind-bending thriller about dreams inside dreams.",
        },
        {
            "title": "Interstellar",
            "year": 2014,
            "director": "Christopher Nolan",
            "genres": ["Sci-Fi", "Drama", "Adventure"],
            "description": "A team travels through a wormhole to find a new home for humanity.",
        },
        {
            "title": "The Dark Knight",
            "year": 2008,
            "director": "Christopher Nolan",
            "genres": ["Action", "Crime", "Drama"],
            "description": "Batman faces the Joker in Gotham City.",
        },
        {
            "title": "Pulp Fiction",
            "year": 1994,
            "director": "Quentin Tarantino",
            "genres": ["Crime", "Drama"],
            "description": "Stories of crime and redemption in Los Angeles.",
        },
        {
            "title": "Django Unchained",
            "year": 2012,
            "director": "Quentin Tarantino",
            "genres": ["Western", "Drama"],
            "description": "A freed slave sets out to rescue his wife.",
        },
        {
            "title": "The Matrix",
            "year": 1999,
            "director": "Lana Wachowski",
            "genres": ["Sci-Fi", "Action"],
            "description": "A hacker discovers the reality is a simulation.",
        },
        {
            "title": "The Shawshank Redemption",
            "year": 1994,
            "director": "Frank Darabont",
            "genres": ["Drama"],
            "description": "Two imprisoned men bond over years, finding solace and redemption.",
        },
        {
            "title": "Forrest Gump",
            "year": 1994,
            "director": "Robert Zemeckis",
            "genres": ["Drama", "Romance"],
            "description": "The life story of Forrest Gump, a man with a big heart.",
        },
        {
            "title": "The Godfather",
            "year": 1972,
            "director": "Francis Ford Coppola",
            "genres": ["Crime", "Drama"],
            "description": "The aging patriarch of an organized crime dynasty transfers control to his son.",
        },
        {
            "title": "Fight Club",
            "year": 1999,
            "director": "David Fincher",
            "genres": ["Drama", "Thriller"],
            "description": "An insomniac office worker forms an underground fight club.",
        },
        {
            "title": "Se7en",
            "year": 1995,
            "director": "David Fincher",
            "genres": ["Crime", "Thriller"],
            "description": "Two detectives hunt a serial killer who uses the seven deadly sins as motives.",
        },
        {
            "title": "Gladiator",
            "year": 2000,
            "director": "Ridley Scott",
            "genres": ["Action", "Drama"],
            "description": "A former Roman general seeks revenge after being betrayed.",
        },
    ]

    for item in movies_data:
        director = get_or_create_director(item["director"])
        movie = get_or_create_movie(item["title"], item["year"])

        movie.description = item["description"]
        movie.director = director
        movie.genres = [get_or_create_genre(g) for g in item["genres"]]

    db.session.commit()

    all_movies = Movie.query.all()

    def add_review(user: User, movie: Movie, rating: int, content: str) -> None:
        existing = Review.query.filter_by(user_id=user.id, movie_id=movie.id).first()
        if not existing:
            db.session.add(
                Review(
                    user_id=user.id,
                    movie_id=movie.id,
                    rating=rating,
                    title=None,
                    content=content,
                )
            )

    add_review(u1, Movie.query.filter_by(title="Inception").first(), 5, "Amazing concept and visuals.")
    add_review(u2, Movie.query.filter_by(title="Inception").first(), 4, "Great movie, a bit confusing at times.")
    add_review(u1, Movie.query.filter_by(title="The Matrix").first(), 5, "Classic. Still holds up.")
    add_review(u2, Movie.query.filter_by(title="The Godfather").first(), 5, "One of the best movies ever.")
    add_review(u1, Movie.query.filter_by(title="Fight Club").first(), 4, "Dark and clever.")

    db.session.commit()

    def add_favorite(user: User, movie: Movie) -> None:
        existing = Favorite.query.filter_by(user_id=user.id, movie_id=movie.id).first()
        if not existing:
            db.session.add(Favorite(user_id=user.id, movie_id=movie.id))

    add_favorite(u1, Movie.query.filter_by(title="Inception").first())
    add_favorite(u1, Movie.query.filter_by(title="Interstellar").first())
    add_favorite(u2, Movie.query.filter_by(title="The Godfather").first())

    db.session.commit()

    to_watch_u1 = get_default_collection(u1.id, "To watch")
    watching_u1 = get_default_collection(u1.id, "Watching")
    watched_u1 = get_default_collection(u1.id, "Watched")

    inception = Movie.query.filter_by(title="Inception").first()
    interstellar = Movie.query.filter_by(title="Interstellar").first()
    matrix = Movie.query.filter_by(title="The Matrix").first()

    if inception not in watched_u1.movies:
        watched_u1.movies.append(inception)

    if interstellar not in to_watch_u1.movies:
        to_watch_u1.movies.append(interstellar)

    if matrix not in watching_u1.movies:
        watching_u1.movies.append(matrix)

    db.session.commit()

    print("Seed done.")
    print("Movies:", Movie.query.count())
    print("Users:", User.query.count())
    print("Reviews:", Review.query.count())
    print("Favorites:", Favorite.query.count())
    print("Collections:", Collection.query.count())
