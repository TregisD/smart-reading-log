INSERT INTO users (name)
VALUES ('Leonardo Guzman')
ON CONFLICT (name) DO NOTHING
RETURNING *;

INSERT INTO books (title, author, pages, genre, published_year, isbn)
VALUES
    ('No Longer Human', 'Osamu Dazai', 177, 'Fiction', 1948, '9780811204811'),
    ('Desire: Vintage Minis', 'Haruki Murakami', 109, 'Fiction', 2017, '9781784872632'),
    ('An Artist of the Floating World', 'Kazuo Ishiguro', 206, 'Historical Fiction', 1986, '9780571225361'),
    ('The Steppenwolf', 'Hermann Hesse', 227, 'Fiction', 1927, '9781324036814'),
    ('Don''t Believe Everything You Think', 'Joseph Nguyen', 192, 'Self Help', 2022, '9798893310153')
ON CONFLICT (isbn) DO NOTHING
RETURNING *;

INSERT INTO reading_log (user_id, book_id, start_date, end_date)
VALUES
    ((SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
        (SELECT book_id FROM books WHERE title = 'No Longer Human'),
        '2025-09-05', '2025-09-20'),
    ((SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
        (SELECT book_id FROM books WHERE title = 'Desire: Vintage Minis'),
        '2025-09-20','2025-09-21'),
    ((SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
        (SELECT book_id FROM books WHERE title = 'An Artist of the Floating World'),
        '2025-09-20', NULL),
    ((SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
        (SELECT book_id FROM books WHERE title = 'The Steppenwolf'),
        NULL, NULL),
    ((SELECT user_id FROM users WHERE name = 'Leonardo Guzman'),
        (SELECT book_id FROM books WHERE title = 'Don''t Believe Everything You Think'),
        NULL, NULL)
ON CONFLICT (user_id, book_id) DO NOTHING
RETURNING *;

INSERT INTO ratings (book_id, story, characters, writing, themes, enjoyment)
VALUES
    ((SELECT book_id FROM books WHERE title = 'No Longer Human'), 4.0, 4.0, 3.5, 4.5, 3.5),
    ((SELECT book_id FROM books WHERE title = 'Desire: Vintage Minis'), 3.5, 3.5, 3.5, 3.0, 4.0)
ON CONFLICT (book_id) DO NOTHING
RETURNING *;