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

cur.close()
conn.close()