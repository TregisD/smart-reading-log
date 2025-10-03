from flask import Flask, render_template
import psycopg2
from datetime import datetime
import os

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
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get reading status counts
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN rl.end_date IS NOT NULL THEN 1 END) as completed,
            COUNT(CASE WHEN rl.start_date IS NOT NULL AND rl.end_date IS NULL THEN 1 END) as reading,
            COUNT(CASE WHEN rl.start_date IS NULL THEN 1 END) as plan_to_read,
            COUNT(*) as total
        FROM books b
        LEFT JOIN reading_log rl ON b.book_id = rl.book_id 
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    stats = cur.fetchone()
    
    # Get average rating
    cur.execute("""
        SELECT ROUND(AVG(overall), 1) as avg_rating
        FROM ratings;
    """)
    avg_rating = cur.fetchone()[0] or 0
    
    # Get total pages read
    cur.execute("""
        SELECT COALESCE(SUM(b.pages), 0) as total_pages
        FROM books b
        JOIN reading_log rl ON b.book_id = rl.book_id
        WHERE rl.end_date IS NOT NULL
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    total_pages = cur.fetchone()[0]
    
    # Get books completed this month
    cur.execute("""
        SELECT COUNT(*) 
        FROM reading_log rl
        WHERE rl.end_date >= DATE_TRUNC('month', CURRENT_DATE)
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    books_this_month = cur.fetchone()[0]
    
    # Get books completed this year
    cur.execute("""
        SELECT COUNT(*) 
        FROM reading_log rl
        WHERE rl.end_date >= DATE_TRUNC('year', CURRENT_DATE)
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    books_this_year = cur.fetchone()[0]
    
    # Calculate average pages per day (total pages / days since member)
    cur.execute("""
        SELECT 
            ROUND(
                COALESCE(SUM(b.pages), 0)::numeric / 
                NULLIF(CURRENT_DATE - MIN(rl.start_date), 0),
                0
            ) as avg_pages_per_day
        FROM reading_log rl
        JOIN books b ON rl.book_id = b.book_id
        WHERE rl.end_date IS NOT NULL
            AND rl.start_date IS NOT NULL
            AND b.pages IS NOT NULL
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    pages_per_day = cur.fetchone()[0] or 0
    
    # Get 3 most recent book updates
    cur.execute("""
        SELECT 
            b.title,
            b.author,
            rl.start_date,
            rl.end_date,
            r.overall,
            CASE
                WHEN rl.end_date IS NOT NULL THEN 'Completed'
                WHEN rl.start_date IS NOT NULL THEN 'Reading'
                ELSE 'Plan to Read'
            END as status,
            COALESCE(rl.end_date, rl.start_date, CURRENT_DATE) as last_update
        FROM books b
        LEFT JOIN reading_log rl ON b.book_id = rl.book_id
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        LEFT JOIN ratings r ON b.book_id = r.book_id
        ORDER BY last_update DESC NULLS LAST
        LIMIT 3;
    """)
    recent_books = cur.fetchall()
    
    # Get member since date (earliest start_date)
    cur.execute("""
        SELECT MIN(start_date) 
        FROM reading_log 
        WHERE user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
            AND start_date IS NOT NULL;
    """)
    member_since = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    # Format the data for the template
    context = {
        'completed': stats[0],
        'reading': stats[1],
        'plan_to_read': stats[2],
        'total_books': stats[3],
        'avg_rating': avg_rating,
        'total_pages': total_pages,
        'books_this_month': books_this_month,
        'books_this_year': books_this_year,
        'pages_per_day': int(pages_per_day),
        'recent_books': recent_books,
        'member_since': member_since
    }
    
    return render_template("index.html", **context)

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
                   ELSE 'Plan_to_Read'
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

@app.route("/analytics")
def show_analytics():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get average rating by category
    cur.execute("""
        SELECT 
            ROUND(AVG(story), 1) as avg_story,
            ROUND(AVG(characters), 1) as avg_characters,
            ROUND(AVG(writing), 1) as avg_writing,
            ROUND(AVG(themes), 1) as avg_themes,
            ROUND(AVG(enjoyment), 1) as avg_enjoyment
        FROM ratings;
    """)
    rating_breakdown = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return render_template("analytics.html", 
                         avg_story=rating_breakdown[0] or 0,
                         avg_characters=rating_breakdown[1] or 0,
                         avg_writing=rating_breakdown[2] or 0,
                         avg_themes=rating_breakdown[3] or 0,
                         avg_enjoyment=rating_breakdown[4] or 0)


if __name__ == "__main__":
    app.run(debug=True)