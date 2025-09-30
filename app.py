from flask import Flask, render_template
import psycopg2

app = Flask(__name__)

# Database connection details
DB_HOST = "localhost"
DB_NAME = "books_db"
DB_USER = "leoguzman"
DB_PASS = ""

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/books")
def show_books():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT title, author, pages, genre FROM books;")
    books = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("books.html", books=books)

@app.route("/ratings")
def show_ratings():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Join books with ratings to get titles and scores
    cur.execute("""
        SELECT b.title, r.story, r.characters, r.writing, r.themes, r.enjoyment, r.overall
        FROM ratings r
        JOIN books b ON r.book_id = b.book_id
        ORDER BY b.title;
    """)
    
    ratings = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("ratings.html", ratings=ratings)

@app.route("/reading_stats")
def show_reading_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT b.title,
               b.author,
               rl.start_date,
               rl.end_date,
               CASE
                   WHEN rl.start_date IS NOT NULL AND rl.end_date IS NOT NULL THEN 'Read'
                   WHEN rl.start_date IS NOT NULL AND rl.end_date IS NULL THEN 'Currently_Reading'
                   ELSE 'Readlist'
               END AS status
        FROM books b
        LEFT JOIN reading_log rl
        ON b.book_id = rl.book_id
          AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        ORDER BY 
            CASE 
                WHEN rl.start_date IS NOT NULL AND rl.end_date IS NOT NULL THEN 1
                WHEN rl.start_date IS NOT NULL AND rl.end_date IS NULL THEN 2
                ELSE 3
            END,
            b.title;
    """)
    
    books = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("reading_stats.html", books=books)


if __name__ == "__main__":
    app.run(debug=True)
