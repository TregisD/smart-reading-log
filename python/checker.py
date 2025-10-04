import csv

print("Checking books.csv...")
with open("../data/books.csv", "r") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        year = row.get("published_year", "").strip()
        if year and (len(year) < 4 or not year.isdigit()):
            print(f"  ⚠️  Row {i}: Bad year '{year}' for book '{row['title']}'")

print("\nChecking reading_log.csv...")
with open("../data/reading_log.csv", "r") as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader, start=1):
        start = row.get("start_date", "").strip()
        end = row.get("end_date", "").strip()
        
        if start and len(start) < 8:  # Valid date is at least YYYY-MM-DD (10 chars)
            print(f"  ⚠️  Row {i}: Bad start_date '{start}' for ISBN '{row['isbn']}'")
        
        if end and len(end) < 8:
            print(f"  ⚠️  Row {i}: Bad end_date '{end}' for ISBN '{row['isbn']}'")

print("\nDone checking!")

import psycopg2

conn = psycopg2.connect(
    dbname="books_db", user="leoguzman", password="", 
    host="localhost", port="5432"
)
cur = conn.cursor()

cur.execute("""
    SELECT MIN(start_date) 
    FROM reading_log 
    WHERE user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        AND start_date IS NOT NULL;
""")
result = cur.fetchone()
print(f"Member since result: {result}")
print(f"Value: {result[0] if result else 'None'}")

conn = psycopg2.connect(dbname="books_db", user="leoguzman", password="", host="localhost", port="5432")
cur = conn.cursor()

# Fix NULL current_pages
cur.execute("""
    UPDATE reading_log
    SET current_page = CASE
        WHEN end_date IS NOT NULL THEN (SELECT pages FROM books WHERE books.book_id = reading_log.book_id)
        WHEN start_date IS NOT NULL AND end_date IS NULL THEN COALESCE(current_page, 0)
        ELSE 0
    END
    WHERE current_page IS NULL;
""")

print(f"Updated {cur.rowcount} rows")

conn.commit()

# Check the results
cur.execute("""
    SELECT b.title, rl.current_page, b.pages, rl.start_date, rl.end_date
    FROM reading_log rl
    JOIN books b ON rl.book_id = b.book_id
    WHERE rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
    ORDER BY b.title;
""")

print("\nFixed reading_log data:")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}/{row[2]} pages")

cur.close()
conn.close()