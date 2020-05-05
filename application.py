import os
import numpy as np

from flask import Flask, session, render_template, jsonify, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from utils import get_goodreads_data

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


@app.route("/")
def index():
    if not 'user_id' in session.keys():
        return render_template("login.html")
    else:
        book_list = db.execute("SELECT id, title, author FROM books LIMIT 50").fetchall()
        return render_template("index.html", book_list=book_list)

@app.route("/login", methods=["GET","POST"])
def login():
    """Check if user exists in database"""
    message = ""
    if request.method =="POST":
        email = request.form.get('email')
        password = request.form.get('password')
        user = db.execute("SELECT * FROM users WHERE email = :email AND password = :password", {"email": email, "password":password}).fetchone()
        if not user:
            #retourner le template avec identifiant n'existe pas
            message="Identifiants invalides"
            return render_template("login.html", message=message, m_type="error")
        else:
            session['user_id'] = user['id']
            return redirect(url_for('index'))
    else:
        return render_template("login.html", message=message)

@app.route("/logout")
def logout():
    """Logout the user """
    session.pop('user_id', None)
    return render_template("logout.html")

@app.route("/signin", methods=["GET","POST"])
def signin():
    """Sign In the user"""
    message = ""
    if request.method =="POST":
        email = request.form.get('email_signin')
        password = request.form.get('password_signin')

        if db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).rowcount == 0:
            db.execute("INSERT INTO users (email, password) VALUES (:email, :password)", {"email":email,"password":password})
            db.commit()
            message = "Compte créé avec succès"
            return render_template("login.html", message=message, m_type="success")
        else:
            message = "Cet identifiant n'est pas disponible"
            return render_template("signin.html",message=message, m_type="error")
    else:
        return render_template("signin.html")


@app.route("/search", methods=["POST"])
def search():
    """return list of books corresponding to search"""
    search = request.form.get('search')
    search_key = "'%" + search + "%'"
    book_list = db.execute("SELECT * FROM books WHERE title LIKE " + search_key + " OR author LIKE " + search_key + " OR isbn LIKE " + search_key).fetchall()
    if len(book_list)>0:
        return render_template("index.html", book_list=book_list)
    else:
        return render_template("index.html", not_found=True)

@app.route("/books/<int:book_id>",methods=["GET", "POST"])
def view_book(book_id):
    """Show reviews of books"""
    #First check is user is connected
    if not 'user_id' in session.keys():
        return render_template("login.html")
    message = ""
    if request.method == "POST":
        review = request.form.get("review")
        grade = request.form.get("grade")
        if (not review) or (not grade):
            message = "Merci de rentrer à la fois un commentaire et une note :)"
        elif db.execute("SELECT * FROM reviews WHERE book_id = :book_id AND user_id = :user_id", {"book_id": book_id,"user_id":session['user_id']}).rowcount > 1:
            message = "Vous ne pouvez pas évaluer deux fois le même livre"
        else:
            db.execute("INSERT INTO reviews (user_id, book_id, review, note) VALUES (:user_id, :book_id, :review, :note)", {"user_id":session['user_id'],"book_id":book_id,"review":review,"note":grade})
            db.commit()
            message = ""

    book = db.execute("SELECT * FROM books WHERE id = :book_id", {'book_id':book_id}).fetchone()
    # Make sure book exists.
    if not book:
        return render_template("error.html", message="No such book.")
    else:
        #get goodreads rating
        gr_count, gr_grade = get_goodreads_data(book['isbn'])
        #Get all reviews.
        review_list = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {'book_id':book_id}).fetchall()
        render_list = []
        for r in review_list:
            elem = {}
            user = db.execute("SELECT * FROM users WHERE id = :id", {"id": r['user_id']}).fetchone()
            elem['author'] = user['email']
            elem['grade'] = r['note']
            elem['content'] = r['review']
            render_list.append(elem)
        return render_template("reviews.html", book = book, review_list=render_list, gr_count=f'{gr_count:,}', gr_grade=gr_grade, message=message)

@app.route("/api/<isbn>")
def book_api(isbn):
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {'isbn':isbn}).fetchone()
    # Make sure book exists.
    if not book:
        return jsonify({"error": "Invalid book_id"}), 422
    else:
        book_reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {'book_id':book['id']}).fetchall()
        avg_grade = np.mean([r['note'] for r in book_reviews])
        return jsonify({
                "title" : book['title'],
                "author" : book['author'],
                "year" : book['year'],
                "isbn" : book['isbn'],
                "review_count" : len(book_reviews),
                "average_score" : avg_grade
        })

@app.route("/api")
def show_api():
    return render_template("api.html")
