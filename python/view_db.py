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

print("=== USERS ===")
cur.execute("SELECT * FROM users;")
for row in cur.fetchall():
    print(row)

print("\n=== BOOKS ===")
cur.execute("SELECT book_id, title, author, isbn FROM books;")
for row in cur.fetchall():
    print(row)

print("\n=== READING LOG ===")
cur.execute("SELECT * FROM reading_log;")
for row in cur.fetchall():
    print(row)

print("\n=== RATINGS ===")
cur.execute("SELECT * FROM ratings;")
for row in cur.fetchall():
    print(row)

print("\n=== COUNTS ===")
cur.execute("SELECT 'users' as table_name, COUNT(*) FROM users UNION ALL SELECT 'books', COUNT(*) FROM books UNION ALL SELECT 'reading_log', COUNT(*) FROM reading_log UNION ALL SELECT 'ratings', COUNT(*) FROM ratings;")
for row in cur.fetchall():
    print(f"{row[0]}: {row[1]} rows")

cur.close()
conn.close()