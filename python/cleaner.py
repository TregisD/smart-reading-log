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

# Clear all data
cur.execute("TRUNCATE ratings, reading_log, books, users RESTART IDENTITY CASCADE;")

conn.commit()
cur.close()
conn.close()

print("✅ Database cleaned!")