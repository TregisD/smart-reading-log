import psycopg2

DB_NAME = "books_db"
DB_USER = "leoguzman"
DB_PASS = ""
DB_HOST = "localhost"
DB_PORT = "5432"

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

# Create schema (only run once!)
cur.execute("""
-- Users table (with CREATE IF NOT EXISTS to be safe)
CREATE TABLE IF NOT EXISTS users (
  user_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

-- Drop and recreate other tables (only on initial setup)
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
  current_page INTEGER,
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

CREATE OR REPLACE VIEW reading_stats AS
SELECT
  rl.log_id,
  rl.user_id,
  u.name,
  rl.book_id,
  b.title,
  b.pages,
  rl.start_date,
  rl.end_date,
  rl.current_page,
  (rl.end_date - rl.start_date) AS days_to_finish,
  CASE
    WHEN (rl.end_date - rl.start_date) > 0 AND b.pages IS NOT NULL
      THEN ROUND( b.pages::numeric / (rl.end_date - rl.start_date)::numeric, 2)
    ELSE NULL
  END AS pages_per_day
FROM reading_log rl
JOIN books b ON rl.book_id = b.book_id
JOIN users u ON rl.user_id = u.user_id;
""")

conn.commit()
cur.close()
conn.close()

print("✅ Schema created successfully!")