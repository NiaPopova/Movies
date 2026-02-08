from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

movie_genres = db.Table(
    "movie_genres",
    db.Column("movie_id", db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
    db.Column("genre_id", db.Integer, db.ForeignKey("genres.id", ondelete="CASCADE"), primary_key=True),
)

collection_movies = db.Table(
    "collection_movies",
    db.Column("collection_id", db.Integer, db.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    db.Column("movie_id", db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True),
)


class Director(db.Model):
    __tablename__ = "directors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)

    movies = db.relationship("Movie", back_populates="director", cascade="all, delete-orphan")


class Movie(db.Model):
    __tablename__ = "movies"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=True, index=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    poster_url = db.Column(db.String(500), nullable=True)
    trailer_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    director_id = db.Column(
        db.Integer,
        db.ForeignKey("directors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    director = db.relationship("Director", back_populates="movies")

    reviews = db.relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    favorites = db.relationship("Favorite", back_populates="movie", cascade="all, delete-orphan")
    genres = db.relationship("Genre", secondary=movie_genres, back_populates="movies")


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # роли: "user" или "admin"
    role = db.Column(db.String(20), nullable=False, default="user", index=True)

    reviews = db.relationship("Review", back_populates="user", cascade="all, delete-orphan")
    favorites = db.relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    collections = db.relationship("Collection", back_populates="user", cascade="all, delete-orphan")


class Collection(db.Model):
    __tablename__ = "collections"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    is_default = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="collections")
    movies = db.relationship("Movie", secondary=collection_movies, backref="collections")


class Genre(db.Model):
    __tablename__ = "genres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)

    movies = db.relationship("Movie", secondary=movie_genres, back_populates="genres")


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    title = db.Column(db.String(120), nullable=True)

    # по изисквания: коментарът може да е празен
    content = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uniq_user_movie_review"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="chk_rating_1_5"),
    )

    user = db.relationship("User", back_populates="reviews")
    movie = db.relationship("Movie", back_populates="reviews")


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = db.Column(db.Integer, db.ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="uniq_user_movie_fav"),
    )

    user = db.relationship("User", back_populates="favorites")
    movie = db.relationship("Movie", back_populates="favorites")
