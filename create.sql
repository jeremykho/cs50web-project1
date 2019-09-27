CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(15) UNIQUE NOT NULL,
    password CHAR(64) NOT NULL,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL
);

CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    year SMALLINT,
    isbn CHAR(10) NOT NULL
);

CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    rating DECIMAL(2,1),
    user_id INTEGER REFERENCES users,
    book_id INTEGER REFERENCES books
);
