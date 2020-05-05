import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def create_users():
    """Create users database"""

    db.execute("CREATE TABLE users ( \
    id SERIAL PRIMARY KEY, \
    email VARCHAR NOT NULL, \
    password VARCHAR NOT NULL)")
    db.commit()
    #print list of tables
    print(engine.table_names())

def create_books():
    """Create books database"""

    db.execute("CREATE TABLE books ( \
    id SERIAL PRIMARY KEY, \
    title VARCHAR NOT NULL, \
    author VARCHAR NOT NULL, \
    isbn VARCHAR NOT NULL, \
    year INTEGER NOT NULL, \
    nb_review INTEGER,\
    avg_review DECIMAL)")

    f = open("books.csv")
    reader = csv.reader(f)
    skip = True
    for isbn, title, author, year in reader:
        if skip: #skip the header row
            skip=False
            continue
        year = int(year)
        db.execute("INSERT INTO books (title, author, isbn, year) VALUES (:title, :author, :isbn, :year)",
                    {"title": title, "author": author, "isbn":isbn, "year": year})
        print(f"Added book {title} by {author} published in {year} with reference {isbn}")

    db.commit()
    #print list of tables
    print(engine.table_names())

def create_reviews():
    """Create reviews database"""
    db.execute("CREATE TABLE reviews ( \
    id SERIAL PRIMARY KEY, \
    user_id INTEGER REFERENCES users, \
    book_id INTEGER REFERENCES books, \
    review VARCHAR NOT NULL, \
    note INTEGER NOT NULL)")
    db.commit()
    #print list of tables
    print(engine.table_names())

if __name__ == "__main__":
    #create_users()
    #create_books()
    #create_reviews()
