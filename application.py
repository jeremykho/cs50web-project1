import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def fetch_book(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
        {"isbn": isbn}).fetchone()
    if book is None:
        render_template("error.html", message="Book does not exist!")
    return book

def fetch_user():
    user_id = session['user_id']
    user = db.execute("SELECT * FROM users WHERE id = :user_id",
        {"user_id":user_id}).fetchone()
    return user

def fetch_review(book_id, user_id):
    review = db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id",
        {"book_id":book_id, "user_id":user_id}).fetchone()
    return review

@app.route("/", methods=["GET"])
def index():
    if 'user_id' in session:
        user = fetch_user()
        return render_template("index.html", name=user["first_name"])
    return redirect(url_for('login'))

@app.route("/register", methods=["GET","POST"])
def register():
    # Check if already logged in
    if 'user_id' in session:
        return redirect(url_for('index'))
    # New registration
    if request.method == "POST":
        # Check for duplicate username
        username = request.form.get("username")
        if db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount > 0:
            return render_template("register.html", error="Username already taken.")
        # Add new user
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")
        db.execute("INSERT INTO users (first_name, last_name, username, password) \
                    VALUES (:first_name, :last_name, :username, :password)",
                    {"first_name":first_name, "last_name":last_name, "username":username, "password":password})
        db.commit()
        return redirect(url_for('login'))
    # Registration page
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    # Check if already logged in
    if 'user_id' in session:
        return redirect(url_for('index'))
    # New login
    if request.method == 'POST':
        # Check login details
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username = :username AND password = :password",
            {"username": username, "password": password}).fetchone()
        if user is None:
            return render_template("login.html", error="Invalid username/password.")
        # Store user info
        session['user_id'] = user['id']
        return redirect(url_for('index'))
    return render_template("login.html")

@app.route("/logout")
def logout():
    # Remove username from session
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route("/results", methods=["POST"])
def results():
    query = request.form.get("query")
    results = db.execute(f"SELECT * FROM books WHERE title LIKE '%{query}%' OR \
                            author LIKE '%{query}%' OR isbn LIKE '%{query}%'").fetchall()
    return render_template("results.html", results=results)

@app.route("/book/<isbn>", methods=["GET"])
def book(isbn):
    if 'user_id' in session:
        user = fetch_user() # Fetch user info
        # Check if book exists
        book = fetch_book(isbn)
        review = fetch_review(book.id, user.id) # Check for existing review

        # Fetch GoodReads data
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                            params={"key": "JH9iy2wj9ikbergydgFqjA", "isbns": isbn})
        gr_data = res.json()
        gr_avg = gr_data['books'][0]['average_rating']
        gr_count = f"{gr_data['books'][0]['work_ratings_count']:,}"

        reviews = db.execute("SELECT reviews.*, users.first_name, users.last_name \
                                FROM reviews LEFT JOIN users ON reviews.user_id = users.id \
                                WHERE book_id = :book_id AND user_id != :user_id",
                                {"book_id":book.id, "user_id":user.id}).fetchall()

        return render_template("book.html", book=book, gr_avg=gr_avg, gr_count=gr_count,
            review=review, reviews=reviews)
    return redirect(url_for('login'))

@app.route("/book/<isbn>/review", methods=["GET","POST"])
def review(isbn):
    if 'user_id' in session:
        user = fetch_user() # Fetch user info
        book = fetch_book(isbn) # Check if book exists
        review = fetch_review(book.id, user.id) # Check for existing review

        if request.method == "POST":
            rating = request.form.get("rating")
            content = request.form.get("content")
            if review is None:
                db.execute("INSERT INTO reviews (rating, content, book_id, user_id) \
                            VALUES (:rating, :content, :book_id, :user_id)",
                            {"rating":rating, "content":content, "book_id":book.id, "user_id":user.id})
            else:
                db.execute("UPDATE reviews SET rating = :rating, content = :content \
                            WHERE book_id = :book_id AND user_id = :user_id",
                            {"rating":rating, "content":content, "book_id":book.id, "user_id":user.id})
            db.commit()
            return redirect(url_for('book', isbn=isbn))

        return render_template("review.html", book=book, review=review)
    return redirect(url_for('login'))

@app.route("/api/<isbn>", methods=["GET"])
def book_api(isbn):
    """ Return details about a book."""
    book = fetch_book(isbn) # Check if book exists
    if book is None:
        return jsonify({"error":"Invalid ISBN or Book not available."}), 404

    # Determine review count and average
    review = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id = book_id",
        {"book_id":book.id}).fetchone()
    review_avg = f"{review[1]:.2f}"

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": isbn,
        "review_count": review.count,
        "average_score": review_avg
    })
