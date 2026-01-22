#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import get_pg_connection, test_pg_connection, print_section, print_success, print_error
import pg8000

print("\n=== Script 1: PostgreSQL ===")
print("Conectare...")
success, result = test_pg_connection()
if success:
    print("  Conectat")
else:
    print(f"  Eroare: {result}")
    exit(1)

print("Creare tabele...")

conn = get_pg_connection()
cursor = conn.cursor()

tables = [
    # Categories
    """
    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Users
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL UNIQUE,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        phone VARCHAR(20),
        address VARCHAR(255),
        city VARCHAR(50),
        country VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Products
    """
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        sku VARCHAR(50) NOT NULL UNIQUE,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        category_id INTEGER REFERENCES categories(id),
        price DECIMAL(10, 2) NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        rating DECIMAL(3, 2) DEFAULT 0,
        review_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Orders
    """
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        order_number VARCHAR(50) NOT NULL UNIQUE,
        user_id INTEGER REFERENCES users(id),
        status VARCHAR(20) DEFAULT 'pending',
        total_amount DECIMAL(12, 2) DEFAULT 0,
        shipping_address VARCHAR(255),
        shipping_city VARCHAR(50),
        shipping_country VARCHAR(50),
        payment_method VARCHAR(50),
        payment_status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    # Order Items
    """
    CREATE TABLE IF NOT EXISTS order_items (
        id SERIAL PRIMARY KEY,
        order_id INTEGER REFERENCES orders(id),
        product_id INTEGER REFERENCES products(id),
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        total_price DECIMAL(10, 2) NOT NULL
    )
    """,
    
    # Reviews
    """
    CREATE TABLE IF NOT EXISTS reviews (
        id SERIAL PRIMARY KEY,
        product_id INTEGER REFERENCES products(id),
        user_id INTEGER REFERENCES users(id),
        rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
        title VARCHAR(255),
        comment TEXT,
        is_verified BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]

table_names = ['categories', 'users', 'products', 'orders', 'order_items', 'reviews']

for sql, name in zip(tables, table_names):
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"  {name} - ok")
    except Exception as e:
        conn.rollback()
        if 'already exists' in str(e).lower():
            print(f"  {name} - exista deja")
        else:
            print(f"  {name} - eroare")

# Indexi
print("Creare indexi...")
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_products_price ON products(price)",
    "CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
    "CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)",
    "CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)",
]

for idx in indexes:
    try:
        cursor.execute(idx)
        conn.commit()
    except:
        conn.rollback()

print("  Indexi creati")

cursor.close()
conn.close()

# Verificare
print("Verificare...")
conn = get_pg_connection()
cursor = conn.cursor()
cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' ORDER BY table_name
""")
tables = cursor.fetchall()
print(f"  {len(tables)} tabele create")

cursor.close()
conn.close()

print("Gata!\n")