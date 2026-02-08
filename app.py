from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from model import db, Movie, Genre, Review, User, Favorite, Director, Collection

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-key-change"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    genre = request.args.get("genre", "").strip()
    director = request.args.get("director", "").strip()

    query = Movie.query

    if q:
        query = query.filter(Movie.title.ilike(f"%{q}%"))

    if director:
        query = query.join(Director).filter(Director.name.ilike(f"%{director}%"))

    if genre:
        query = query.join(Movie.genres).filter(Genre.name.ilike(f"%{genre}%"))

    movies = query.order_by(Movie.created_at.desc()).all()
    return render_template("index.html", movies=movies, q=q, genre=genre, director=director)


@app.route("/movies/<int:movie_id>")
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    ratings = [r.rating for r in movie.reviews]
    avg = round(sum(ratings) / len(ratings), 2) if ratings else None

    user_collections = []
    if current_user.is_authenticated:
        ensure_default_collections(current_user.id)
        user_collections = (
            Collection.query
            .filter_by(user_id=current_user.id)
            .order_by(Collection.is_default.desc(), Collection.name.asc())
            .all()
        )

    return render_template("movie_detail.html", movie=movie, avg=avg, user_collections=user_collections)


@app.route("/add-movie", methods=["GET", "POST"])
@login_required
def add_movie():
    if getattr(current_user, "role", "user") != "admin":
        flash("Only admin can add movies.")
        return redirect(url_for("index"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        year = request.form.get("year", "").strip()
        description = request.form.get("description", "").strip()
        poster_url = request.form.get("poster_url", "").strip()
        genres_raw = request.form.get("genres", "").strip()
        director_name = request.form.get("director", "").strip()

        if not title:
            flash("Title is required.")
            return redirect(url_for("add_movie"))

        movie = Movie(
            title=title,
            year=int(year) if year.isdigit() else None,
            description=description or None,
            poster_url=poster_url or None,
        )

        if director_name:
            d = Director.query.filter_by(name=director_name).first()
            if not d:
                d = Director(name=director_name)
            movie.director = d

        if genres_raw:
            names = [x.strip() for x in genres_raw.split(",") if x.strip()]
            genre_objs = []
            for name in names:
                g = Genre.query.filter_by(name=name).first()
                if not g:
                    g = Genre(name=name)
                genre_objs.append(g)
            movie.genres = genre_objs

        db.session.add(movie)
        db.session.commit()
        return redirect(url_for("movie_detail", movie_id=movie.id))

    return render_template("add_movie.html")


@app.route("/movies/<int:movie_id>/review", methods=["POST"])
@login_required
def add_review(movie_id):
    Movie.query.get_or_404(movie_id)

    rating_raw = request.form.get("rating", "").strip()
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()

    if not rating_raw.isdigit():
        flash("Rating must be 1–5.")
        return redirect(url_for("movie_detail", movie_id=movie_id))

    rating = int(rating_raw)
    if rating < 1 or rating > 5:
        flash("Rating must be 1–5.")
        return redirect(url_for("movie_detail", movie_id=movie_id))

    existing = Review.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        existing.rating = rating
        existing.title = title or None
        existing.content = content or None
        flash("Review updated.")
    else:
        db.session.add(
            Review(
                rating=rating,
                title=title or None,
                content=content or None,
                user_id=current_user.id,
                movie_id=movie_id,
            )
        )
        flash("Review added.")

    db.session.commit()
    return redirect(url_for("movie_detail", movie_id=movie_id))


@app.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    is_owner = review.user_id == current_user.id
    is_admin = getattr(current_user, "role", "user") == "admin"

    if not (is_owner or is_admin):
        flash("No permission.")
        return redirect(url_for("movie_detail", movie_id=review.movie_id))

    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.")
    return redirect(url_for("movie_detail", movie_id=review.movie_id))


@app.route("/movies/<int:movie_id>/favorite", methods=["POST"])
@login_required
def favorite_movie(movie_id):
    Movie.query.get_or_404(movie_id)

    existing = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if existing:
        flash("Already in favorites.")
        return redirect(url_for("movie_detail", movie_id=movie_id))

    db.session.add(Favorite(user_id=current_user.id, movie_id=movie_id))
    db.session.commit()
    flash("Added to favorites.")
    return redirect(url_for("movie_detail", movie_id=movie_id))


@app.route("/movies/<int:movie_id>/unfavorite", methods=["POST"])
@login_required
def unfavorite_movie(movie_id):
    Movie.query.get_or_404(movie_id)

    existing = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
    if not existing:
        flash("Not in favorites.")
        return redirect(url_for("movie_detail", movie_id=movie_id))

    db.session.delete(existing)
    db.session.commit()
    flash("Removed from favorites.")
    return redirect(url_for("movie_detail", movie_id=movie_id))


@app.route("/profile")
@login_required
def profile():
    ensure_default_collections(current_user.id)

    my_reviews = Review.query.filter_by(user_id=current_user.id).order_by(Review.created_at.desc()).all()
    my_favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.id.desc()).all()

    collections = (
        Collection.query
        .filter_by(user_id=current_user.id)
        .order_by(Collection.is_default.desc(), Collection.name.asc())
        .all()
    )

    return render_template(
        "profile.html",
        my_reviews=my_reviews,
        my_favorites=my_favorites,
        collections=collections,
    )


@app.route("/collections/<int:collection_id>")
@login_required
def collection_detail(collection_id):
    c = Collection.query.get_or_404(collection_id)
    if c.user_id != current_user.id:
        flash("No access.")
        return redirect(url_for("profile"))
    return render_template("collection_detail.html", c=c)


@app.route("/collections/create", methods=["POST"])
@login_required
def create_collection():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Name required.")
        return redirect(url_for("profile"))

    db.session.add(Collection(user_id=current_user.id, name=name, is_default=False))
    db.session.commit()
    flash("Collection created.")
    return redirect(url_for("profile"))


@app.route("/collections/<int:collection_id>/rename", methods=["POST"])
@login_required
def rename_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    if c.user_id != current_user.id:
        flash("No access.")
        return redirect(url_for("profile"))

    if c.is_default:
        flash("Default collections cannot be renamed.")
        return redirect(url_for("profile"))

    new_name = request.form.get("name", "").strip()
    if not new_name:
        flash("Name required.")
        return redirect(url_for("profile"))

    c.name = new_name
    db.session.commit()
    flash("Collection renamed.")
    return redirect(url_for("profile"))


@app.route("/collections/<int:collection_id>/delete", methods=["POST"])
@login_required
def delete_collection(collection_id):
    c = Collection.query.get_or_404(collection_id)
    if c.user_id != current_user.id:
        flash("No access.")
        return redirect(url_for("profile"))

    if c.is_default:
        flash("Default collections cannot be deleted.")
        return redirect(url_for("profile"))

    db.session.delete(c)
    db.session.commit()
    flash("Collection deleted.")
    return redirect(url_for("profile"))


@app.route("/collections/<int:collection_id>/add/<int:movie_id>", methods=["POST"])
@login_required
def add_movie_to_collection(collection_id, movie_id):
    c = Collection.query.get_or_404(collection_id)
    if c.user_id != current_user.id:
        flash("No access.")
        return redirect(url_for("profile"))

    m = Movie.query.get_or_404(movie_id)

    # default колекциите са взаимоизключващи
    if c.is_default:
        other_defaults = Collection.query.filter_by(user_id=current_user.id, is_default=True).all()
        for od in other_defaults:
            if od.id != c.id and m in od.movies:
                od.movies.remove(m)

    if m not in c.movies:
        c.movies.append(m)
        db.session.commit()
        flash("Added to collection.")
    else:
        flash("Already in collection.")

    return redirect(url_for("movie_detail", movie_id=movie_id))


@app.route("/movies/<int:movie_id>/add-to-collection", methods=["POST"])
@login_required
def add_to_collection_from_movie(movie_id):
    collection_id = request.form.get("collection_id", "").strip()
    if not collection_id.isdigit():
        flash("Invalid collection.")
        return redirect(url_for("movie_detail", movie_id=movie_id))

    return add_movie_to_collection(int(collection_id), movie_id)


@app.route("/collections/<int:collection_id>/remove/<int:movie_id>", methods=["POST"])
@login_required
def remove_movie_from_collection(collection_id, movie_id):
    c = Collection.query.get_or_404(collection_id)
    if c.user_id != current_user.id:
        flash("No access.")
        return redirect(url_for("profile"))

    m = Movie.query.get_or_404(movie_id)

    if m in c.movies:
        c.movies.remove(m)
        db.session.commit()
        flash("Removed from collection.")
    else:
        flash("Movie not in this collection.")

    return redirect(url_for("collection_detail", collection_id=collection_id))


@app.route("/directors")
def directors_list():
    q = request.args.get("q", "").strip()
    query = Director.query
    if q:
        query = query.filter(Director.name.ilike(f"%{q}%"))
    directors = query.order_by(Director.name.asc()).all()
    return render_template("directors.html", directors=directors, q=q)


@app.route("/directors/<int:director_id>")
def director_detail(director_id):
    director = Director.query.get_or_404(director_id)
    movies = Movie.query.filter_by(director_id=director.id).order_by(Movie.year.desc()).all()
    return render_template("director_detail.html", director=director, movies=movies)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3:
            flash("Username must be at least 3 chars.")
            return redirect(url_for("register"))

        if "@" not in email or len(email) < 5:
            flash("Invalid email.")
            return redirect(url_for("register"))

        if len(password) < 4:
            flash("Password must be at least 4 chars.")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already used.")
            return redirect(url_for("register"))

        user = User(
            username=username,
            email=email,
            # pbkdf2 => няма да ти крашва със scrypt
            password=generate_password_hash(password, method="pbkdf2:sha256", salt_length=16),
            role="user",
        )

        db.session.add(user)
        db.session.commit()
        ensure_default_collections(user.id)

        flash("Registered! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("No such user.")
            return redirect(url_for("login"))

        if not check_password_hash(user.password, password):
            flash("Wrong password.")
            return redirect(url_for("login"))

        login_user(user)
        flash("Logged in.")
        return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
