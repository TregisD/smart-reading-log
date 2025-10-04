from flask import Flask, render_template, request, jsonify
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
    
    # Get reading status counts (based on current_page)
    cur.execute("""
        SELECT 
            COUNT(CASE WHEN COALESCE(rl.current_page, 0) = b.pages THEN 1 END) as completed,
            COUNT(CASE WHEN COALESCE(rl.current_page, 0) > 0 AND COALESCE(rl.current_page, 0) < b.pages THEN 1 END) as reading,
            COUNT(CASE WHEN COALESCE(rl.current_page, 0) = 0 THEN 1 END) as plan_to_read,
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
        SELECT COALESCE(SUM(rl.current_page), 0) as total_pages
        FROM books b
        JOIN reading_log rl ON b.book_id = rl.book_id
        WHERE rl.start_date IS NOT NULL
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    total_pages = cur.fetchone()[0]
    
    # Get books completed this month (based on current_page = total pages)
    cur.execute("""
        SELECT COUNT(*) 
        FROM reading_log rl
        JOIN books b ON rl.book_id = b.book_id
        WHERE rl.current_page = b.pages
            AND rl.end_date >= DATE_TRUNC('month', CURRENT_DATE)
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    books_this_month = cur.fetchone()[0]
    
    # Get books completed this year (based on current_page = total pages)
    cur.execute("""
        SELECT COUNT(*) 
        FROM reading_log rl
        JOIN books b ON rl.book_id = b.book_id
        WHERE rl.current_page = b.pages
            AND rl.end_date >= DATE_TRUNC('year', CURRENT_DATE)
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman');
    """)
    books_this_year = cur.fetchone()[0]
    
    # Calculate average pages per day (total pages read / days since member)
    cur.execute("""
        SELECT 
            ROUND(
                COALESCE(SUM(COALESCE(rl.current_page, 0)), 0)::numeric / 
                NULLIF(CURRENT_DATE - MIN(
                    CASE WHEN rl.current_page > 0 THEN rl.start_date ELSE NULL END
                ), 0),
                0
            ) as avg_pages_per_day
        FROM reading_log rl
        JOIN books b ON rl.book_id = b.book_id
        WHERE rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
            AND COALESCE(rl.current_page, 0) > 0;
    """)
    pages_per_day = cur.fetchone()[0] or 0
    
    # Get 3 most recent book updates (based on when current_page was last changed)
    cur.execute("""
        SELECT 
            b.title,
            b.author,
            rl.start_date,
            rl.end_date,
            r.overall,
            CASE
                WHEN COALESCE(rl.current_page, 0) = b.pages THEN 'Completed'
                WHEN COALESCE(rl.current_page, 0) > 0 THEN 'Reading'
                ELSE 'Plan to Read'
            END as status,
            COALESCE(rl.end_date, rl.start_date, CURRENT_DATE) as last_update
        FROM books b
        LEFT JOIN reading_log rl ON b.book_id = rl.book_id
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        LEFT JOIN ratings r ON b.book_id = r.book_id
        WHERE COALESCE(rl.current_page, 0) > 0
        ORDER BY last_update DESC NULLS LAST
        LIMIT 3;
    """)
    recent_books = cur.fetchall()
    
    # Get member since date (earliest start_date where current_page > 0)
    cur.execute("""
        SELECT MIN(start_date) 
        FROM reading_log 
        WHERE user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
            AND start_date IS NOT NULL
            AND current_page > 0;
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
    
    # First, ensure all books have a reading_log entry (with current_page = 0)
    cur.execute("""
        INSERT INTO reading_log (user_id, book_id, current_page, start_date, end_date)
        SELECT 
            (SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
            b.book_id,
            0,
            NULL,
            NULL
        FROM books b
        WHERE NOT EXISTS (
            SELECT 1 FROM reading_log rl 
            WHERE rl.book_id = b.book_id 
                AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        )
        ON CONFLICT (user_id, book_id) DO NOTHING;
    """)
    conn.commit()
    
    # Get all books with their reading status, ratings, and page progress
    cur.execute("""
        SELECT 
            b.book_id,
            b.title,
            b.author,
            b.pages,
            b.genre,
            rl.start_date,
            rl.end_date,
            COALESCE(rl.current_page, 0) as current_page,
            r.overall,
            r.story,
            r.characters,
            r.writing,
            r.themes,
            r.enjoyment,
            CASE
                WHEN COALESCE(rl.current_page, 0) = b.pages THEN 'Completed'
                WHEN COALESCE(rl.current_page, 0) > 0 AND COALESCE(rl.current_page, 0) < b.pages THEN 'Reading'
                ELSE 'Plan to Read'
            END AS status
        FROM books b
        LEFT JOIN reading_log rl ON b.book_id = rl.book_id
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        LEFT JOIN ratings r ON b.book_id = r.book_id
        ORDER BY 
            CASE 
                WHEN COALESCE(rl.current_page, 0) = b.pages THEN 1
                WHEN COALESCE(rl.current_page, 0) > 0 AND COALESCE(rl.current_page, 0) < b.pages THEN 2
                ELSE 3
            END,
            b.title;
    """)
    
    books = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template("books.html", books=books)

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

@app.route("/add_book")
def add_book_page():
    return render_template("add_book.html")

@app.route("/add_book", methods=["POST"])
def add_book():
    from flask import request, jsonify
    
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert book
        cur.execute("""
            INSERT INTO books (title, author, pages, genre, published_year, isbn)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (isbn) DO UPDATE 
            SET title = EXCLUDED.title,
                author = EXCLUDED.author,
                pages = EXCLUDED.pages,
                genre = EXCLUDED.genre,
                published_year = EXCLUDED.published_year
            RETURNING book_id;
        """, (
            data['title'],
            data['author'],
            int(data['pages']),
            data['genre'],
            int(data['published_year']) if data.get('published_year') else None,
            data['isbn']
        ))
        
        book_id = cur.fetchone()[0]
        
        # Get or create user
        cur.execute("""
            INSERT INTO users (name)
            VALUES ('Leonardo Guzman')
            ON CONFLICT (name) DO NOTHING;
        """)
        
        # Insert or update reading_log
        start_date = data.get('start_date') if data.get('start_date') else None
        end_date = data.get('end_date') if data.get('end_date') else None
        current_page = int(data.get('current_page', 0))
        
        cur.execute("""
            INSERT INTO reading_log (user_id, book_id, start_date, end_date, current_page)
            VALUES (
                (SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
                %s, %s, %s, %s
            )
            ON CONFLICT (user_id, book_id) DO UPDATE
            SET start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                current_page = EXCLUDED.current_page;
        """, (book_id, start_date, end_date, current_page))
        
        # Insert or update ratings if provided
        if all(data.get(cat) for cat in ['story', 'characters', 'writing', 'themes', 'enjoyment']):
            cur.execute("""
                INSERT INTO ratings (book_id, story, characters, writing, themes, enjoyment)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (book_id) DO UPDATE
                SET story = EXCLUDED.story,
                    characters = EXCLUDED.characters,
                    writing = EXCLUDED.writing,
                    themes = EXCLUDED.themes,
                    enjoyment = EXCLUDED.enjoyment;
            """, (
                book_id,
                float(data['story']),
                float(data['characters']),
                float(data['writing']),
                float(data['themes']),
                float(data['enjoyment'])
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Book added successfully!"})
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/edit_book/<int:book_id>")
def edit_book_page(book_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get book data
    cur.execute("""
        SELECT 
            b.book_id, b.title, b.author, b.pages, b.genre, b.published_year, b.isbn,
            rl.start_date, rl.end_date, COALESCE(rl.current_page, 0),
            r.story, r.characters, r.writing, r.themes, r.enjoyment
        FROM books b
        LEFT JOIN reading_log rl ON b.book_id = rl.book_id
            AND rl.user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        LEFT JOIN ratings r ON b.book_id = r.book_id
        WHERE b.book_id = %s;
    """, (book_id,))
    
    book = cur.fetchone()
    cur.close()
    conn.close()
    
    if not book:
        return "Book not found", 404
    
    return render_template("edit_book.html", book=book)

@app.route("/edit_book/<int:book_id>", methods=["POST"])
def edit_book(book_id):
    from flask import request, jsonify
    
    data = request.get_json()
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Update book
        cur.execute("""
            UPDATE books 
            SET title = %s, author = %s, pages = %s, genre = %s, 
                published_year = %s, isbn = %s
            WHERE book_id = %s;
        """, (
            data['title'],
            data['author'],
            int(data['pages']),
            data['genre'],
            int(data['published_year']) if data.get('published_year') else None,
            data['isbn'],
            book_id
        ))
        
        # Update reading_log
        start_date = data.get('start_date') if data.get('start_date') else None
        end_date = data.get('end_date') if data.get('end_date') else None
        current_page = int(data.get('current_page', 0))
        
        cur.execute("""
            INSERT INTO reading_log (user_id, book_id, start_date, end_date, current_page)
            VALUES (
                (SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
                %s, %s, %s, %s
            )
            ON CONFLICT (user_id, book_id) DO UPDATE
            SET start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                current_page = EXCLUDED.current_page;
        """, (book_id, start_date, end_date, current_page))
        
        # Update or insert ratings if provided
        if all(data.get(cat) for cat in ['story', 'characters', 'writing', 'themes', 'enjoyment']):
            cur.execute("""
                INSERT INTO ratings (book_id, story, characters, writing, themes, enjoyment)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (book_id) DO UPDATE
                SET story = EXCLUDED.story,
                    characters = EXCLUDED.characters,
                    writing = EXCLUDED.writing,
                    themes = EXCLUDED.themes,
                    enjoyment = EXCLUDED.enjoyment;
            """, (
                book_id,
                float(data['story']),
                float(data['characters']),
                float(data['writing']),
                float(data['themes']),
                float(data['enjoyment'])
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True, "message": "Book updated successfully!"})
        
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/update_progress", methods=["POST"])
def update_progress():
    from flask import request, jsonify
    
    data = request.get_json()
    book_id = data.get('book_id')
    current_page = data.get('current_page')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get the total pages for this book
        cur.execute("SELECT pages FROM books WHERE book_id = %s", (book_id,))
        result = cur.fetchone()
        total_pages = result[0] if result else None
        
        # Check if reading_log entry exists
        cur.execute("""
            SELECT log_id FROM reading_log 
            WHERE book_id = %s 
                AND user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
        """, (book_id,))
        
        log_exists = cur.fetchone()
        
        # Determine if book is completed
        is_completed = (current_page == total_pages)
        
        if log_exists:
            # Update existing entry
            if is_completed:
                cur.execute("""
                    UPDATE reading_log 
                    SET current_page = %s,
                        start_date = COALESCE(start_date, CURRENT_DATE),
                        end_date = CURRENT_DATE
                    WHERE book_id = %s 
                        AND user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
                """, (current_page, book_id))
            elif current_page > 0:
                cur.execute("""
                    UPDATE reading_log 
                    SET current_page = %s,
                        start_date = COALESCE(start_date, CURRENT_DATE),
                        end_date = NULL
                    WHERE book_id = %s 
                        AND user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
                """, (current_page, book_id))
            else:
                cur.execute("""
                    UPDATE reading_log 
                    SET current_page = 0,
                        start_date = NULL,
                        end_date = NULL
                    WHERE book_id = %s 
                        AND user_id = (SELECT user_id FROM users WHERE name = 'Leonardo Guzman')
                """, (book_id,))
        else:
            # Insert new entry
            if is_completed:
                cur.execute("""
                    INSERT INTO reading_log (user_id, book_id, current_page, start_date, end_date)
                    VALUES (
                        (SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
                        %s, %s, CURRENT_DATE, CURRENT_DATE
                    )
                """, (book_id, current_page))
            elif current_page > 0:
                cur.execute("""
                    INSERT INTO reading_log (user_id, book_id, current_page, start_date, end_date)
                    VALUES (
                        (SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
                        %s, %s, CURRENT_DATE, NULL
                    )
                """, (book_id, current_page))
            else:
                cur.execute("""
                    INSERT INTO reading_log (user_id, book_id, current_page, start_date, end_date)
                    VALUES (
                        (SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
                        %s, 0, NULL, NULL
                    )
                """, (book_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({"success": False, "error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)