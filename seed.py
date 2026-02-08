from __future__ import annotations

from app import app
from model import db, Movie, Genre, Director


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


with app.app_context():
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
    print("Seed done. Movies in DB:", Movie.query.count())
