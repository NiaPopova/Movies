# OUR MOVIES (Goodreads-style for Movies)

Flask web app where users can browse movies, leave reviews, add favorites, and organize movies into collections.

## Features
- Movies list + search by title, genre, director
- Movie detail page (poster, genres, director, average rating)
- Reviews (1–5), update own review, delete own review
- Favorites
- Collections:
  - 3 default collections: To watch / Watching / Watched
  - Default collections are mutually exclusive
  - Custom collections (create / rename / delete)
  - Add/remove movies from collections
- Directors pages
- Roles:
  - user
  - admin (can add movies, can delete any review)

## Installation

### 1) Create virtual environment

macOS / Linux:
    python -m venv .venv
    source .venv/bin/activate

Windows (PowerShell):
    python -m venv .venv
    .venv\Scripts\Activate.ps1

### 2) Install dependencies
    pip install -r requirements.txt

### 3) Run the app
    python app.py

Open:
http://127.0.0.1:5000

## Database reset (if needed)

If you changed models and the app crashes, delete the database file:

macOS / Linux:
    rm movies.db

Windows:
    del movies.db

Then run again:
    python app.py

## Seed sample data (optional)

    python seed.py

This creates:
- admin user: admin / admin123
- sample users
- movies, directors, genres
- reviews, favorites, collections

## Run tests

    pytest

## Run tests with coverage

    coverage run -m pytest
    coverage report -m
