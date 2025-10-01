import psycopg2
import csv

DB_NAME = "books_db"
DB_USER = "leoguzman"
DB_PASS = ""
DB_HOST = "localhost"
DB_PORT = "5432"

conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
)
cur = conn.cursor()

# ---------- Load Users ----------
print("Loading users...")
with open("../data/users.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("""
            INSERT INTO users (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING;
        """, (row["name"].strip(),))
conn.commit()
print("✅ Users loaded")

# ---------- Load Books ----------
print("Loading books...")
with open("../data/books.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        cur.execute("""
            INSERT INTO books (title, author, pages, genre, published_year, isbn)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (isbn) DO NOTHING;
        """, (row["title"].strip(), 
              row["author"].strip(), 
              row["pages"].strip() if row["pages"] else None,
              row["genre"].strip(), 
              row["published_year"].strip() if row["published_year"] else None,
              row["isbn"].strip()))
conn.commit()
print("✅ Books loaded")

# ---------- Load Reading Log ----------
print("Loading reading log...")
with open("../data/reading_log.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        isbn = row["isbn"].strip()
        user_name = row["user_name"].strip()
        
        # Check if book exists
        cur.execute("SELECT book_id FROM books WHERE isbn = %s", (isbn,))
        book = cur.fetchone()
        
        if not book:
            print(f"⚠️  WARNING: Book with ISBN '{isbn}' not found. Skipping reading log entry for user '{user_name}'")
            continue
        
        # Check if user exists
        cur.execute("SELECT user_id FROM users WHERE name = %s", (user_name,))
        user = cur.fetchone()
        
        if not user:
            print(f"⚠️  WARNING: User '{user_name}' not found. Skipping reading log entry.")
            continue
        
        cur.execute("""
            INSERT INTO reading_log (user_id, book_id, start_date, end_date)
            VALUES (
                (SELECT user_id FROM users WHERE name = %s),
                (SELECT book_id FROM books WHERE isbn = %s),
                NULLIF(%s, '')::DATE,
                NULLIF(%s, '')::DATE
            )
            ON CONFLICT (user_id, book_id) DO UPDATE
            SET start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date;
        """, (user_name, isbn, row["start_date"].strip(), row["end_date"].strip()))
conn.commit()
print("✅ Reading log loaded")

# ---------- Load Ratings ----------
print("Loading ratings...")
with open("../data/ratings.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        isbn = row["isbn"].strip()
        
        # Check if book exists
        cur.execute("SELECT book_id FROM books WHERE isbn = %s", (isbn,))
        book = cur.fetchone()
        
        if not book:
            print(f"⚠️  WARNING: Book with ISBN '{isbn}' not found. Skipping rating.")
            continue
        
        cur.execute("""
            INSERT INTO ratings (book_id, story, characters, writing, themes, enjoyment)
            VALUES (
                (SELECT book_id FROM books WHERE isbn = %s),
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (book_id) DO NOTHING;
        """, (isbn, 
              row["story"].strip(), 
              row["characters"].strip(),
              row["writing"].strip(), 
              row["themes"].strip(), 
              row["enjoyment"].strip()))
conn.commit()
print("✅ Ratings loaded")

cur.close()
conn.close()

print("\n✅ Data loaded successfully!")