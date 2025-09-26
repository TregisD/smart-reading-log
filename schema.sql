-- Tables
CREATE TABLE IF NOT EXISTS users (
  user_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

-- Drop old tables if they exist (so you can re-run this safely)
DROP TABLE IF EXISTS ratings CASCADE;
DROP TABLE IF EXISTS reading_log CASCADE;
DROP TABLE IF EXISTS books CASCADE;

CREATE TABLE books (
  book_id SERIAL PRIMARY KEY,
  title TEXT NOT NULL,
  author TEXT,
  pages INTEGER,
  genre TEXT,
  published_year SMALLINT,
  isbn TEXT NOT NULL UNIQUE
);

CREATE TABLE reading_log (
  log_id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
  start_date DATE,
  end_date DATE,
  UNIQUE (user_id, book_id)
);

CREATE TABLE ratings (
    rating_id SERIAL PRIMARY KEY,
    book_id INT REFERENCES books(book_id),  
    story NUMERIC(2,1)
        CHECK (story >= 1.0 AND story <= 5.0)
        CHECK ((story * 10) % 5 = 0),
    characters NUMERIC(2,1) 
        CHECK (characters >= 1.0 AND characters <= 5.0)
        CHECK ((characters * 10) % 5 = 0),
    writing NUMERIC(2,1) 
        CHECK (writing >= 1.0 AND writing <= 5.0)
        CHECK ((writing * 10) % 5 = 0),
    themes NUMERIC(2,1) 
        CHECK (themes >= 1.0 AND themes <= 5.0)
        CHECK ((themes * 10) % 5 = 0),
    enjoyment NUMERIC(2,1) 
        CHECK (enjoyment >= 1.0 AND enjoyment <= 5.0)
        CHECK ((enjoyment * 10) % 5 = 0),
    overall NUMERIC(2,1) GENERATED ALWAYS AS 
        ((story + characters + writing + themes + enjoyment) / 5.0) STORED,
    UNIQUE (book_id)
);

-- Helpful view: reading stats (days_to_finish, pages_per_day)
CREATE VIEW reading_stats AS
SELECT
  rl.log_id,
  rl.user_id,
  u.name,
  rl.book_id,
  b.title,
  b.pages,
  rl.start_date,
  rl.end_date,
  (rl.end_date - rl.start_date) AS days_to_finish,
  CASE
    WHEN (rl.end_date - rl.start_date) > 0 AND b.pages IS NOT NULL
      THEN ROUND( b.pages::numeric / (rl.end_date - rl.start_date)::numeric, 2)
    ELSE NULL
  END AS pages_per_day
FROM reading_log rl
JOIN books b ON rl.book_id = b.book_id
JOIN users u ON rl.user_id = u.user_id;
