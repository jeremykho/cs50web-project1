CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL,
    password PASSWORD NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    rating DECIMAL(2,1),
    user_id INTEGER REFERENCES users,
    book_id INTEGER REFERENCES books,
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER,
    isbn INTEGER NOT NULL,
);