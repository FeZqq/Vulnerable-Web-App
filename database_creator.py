import sqlite3
# This script creates a SQLite database with two tables: products and users.
# Just run this script to set up the database.
conn = sqlite3.connect('database.db')   
c = conn.cursor()

c.execute('DROP TABLE IF EXISTS products')
c.execute('''
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    category TEXT
)
''')

c.execute('DROP TABLE IF EXISTS users')
c.execute('''
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    email TEXT,
    credit_card TEXT
)
''')

c.executemany('INSERT INTO products (name, category) VALUES (?, ?)', [
    ('Apple', 'Fruit'),
    ('Banana', 'Fruit'),
    ('Carrot', 'Vegetable'),
    ('Laptop', 'Electronics'),
    ('Phone', 'Electronics'),
    ('Headphones', 'Electronics'),
    ('Orange Juice', 'Beverage'),
    ('Coffee', 'Beverage'),
    ('Desk', 'Furniture'),
    ('Chair', 'Furniture')
])

c.executemany('INSERT INTO users (username, password, email, credit_card) VALUES (?, ?, ?, ?)', [
    ('admin', 'admin123', 'admin@example.com', '4111 1111 1111 1111'),
    ('alice', 'alicepass', 'alice@example.com', '5500 0000 0000 0004'),
    ('bob', 'bobsecure', 'bob@example.com', '3400 0000 0000 009'),
    ('eve', 'evehack', 'eve@example.com', '3000 0000 0000 04'),
    ('user', 'password', 'user@example.com', '6011 0000 0000 0004'),
])

conn.commit()
conn.close()