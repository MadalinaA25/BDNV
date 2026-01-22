#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    get_pg_connection, get_mongo_connection,
    generate_categories, generate_users, generate_products,
    generate_orders, generate_order_items, generate_reviews,
    print_section, print_success, print_error, print_info
)

print("\n=== Script 3: Populare Date ===")
print("Generare date...")
categories = generate_categories()
print(f"  {len(categories)} categorii")

users = generate_users(100)
print(f"  {len(users)} useri")

products = generate_products(200)
print(f"  {len(products)} produse")

orders = generate_orders(users, 150)
print(f"  {len(orders)} comenzi")

order_items = generate_order_items(orders, products)
print(f"  {len(order_items)} items")

reviews = generate_reviews(users, products, 80)
print(f"  {len(reviews)} reviews")

print("\nInsert PostgreSQL...")

pg_conn = get_pg_connection()
pg_cursor = pg_conn.cursor()

# Clear existing data
for table in ['reviews', 'order_items', 'orders', 'products', 'users', 'categories']:
    pg_cursor.execute(f"DELETE FROM {table}")
pg_conn.commit()

for cat in categories:
    pg_cursor.execute(
        "INSERT INTO categories (id, name, description) VALUES (%s, %s, %s)",
        (cat['id'], cat['name'], cat['description'])
    )
pg_conn.commit()

for user in users:
    pg_cursor.execute("""
        INSERT INTO users (id, username, email, first_name, last_name, phone, address, city, country, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (user['id'], user['username'], user['email'], user['first_name'], user['last_name'],
          user['phone'], user['address'], user['city'], user['country'], user['created_at']))
pg_conn.commit()

for prod in products:
    pg_cursor.execute("""
        INSERT INTO products (id, sku, name, description, category_id, price, stock_quantity, rating, review_count, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (prod['id'], prod['sku'], prod['name'], prod['description'], prod['category_id'],
          prod['price'], prod['stock_quantity'], prod['rating'], prod['review_count'], prod['created_at']))
pg_conn.commit()

for order in orders:
    pg_cursor.execute("""
        INSERT INTO orders (id, order_number, user_id, status, total_amount, shipping_address, 
                           shipping_city, shipping_country, payment_method, payment_status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (order['id'], order['order_number'], order['user_id'], order['status'], order['total_amount'],
          order['shipping_address'], order['shipping_city'], order['shipping_country'],
          order['payment_method'], order['payment_status'], order['created_at']))
pg_conn.commit()

for item in order_items:
    pg_cursor.execute("""
        INSERT INTO order_items (id, order_id, product_id, quantity, unit_price, total_price)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (item['id'], item['order_id'], item['product_id'], item['quantity'], 
          item['unit_price'], item['total_price']))
pg_conn.commit()

for review in reviews:
    pg_cursor.execute("""
        INSERT INTO reviews (id, product_id, user_id, rating, title, comment, is_verified, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (review['id'], review['product_id'], review['user_id'], review['rating'],
          review['title'], review['comment'], review['is_verified'], review['created_at']))
pg_conn.commit()
print("  PostgreSQL - gata")

# Reset sequences
pg_cursor.execute("SELECT setval('categories_id_seq', (SELECT MAX(id) FROM categories))")
pg_cursor.execute("SELECT setval('users_id_seq', (SELECT MAX(id) FROM users))")
pg_cursor.execute("SELECT setval('products_id_seq', (SELECT MAX(id) FROM products))")
pg_cursor.execute("SELECT setval('orders_id_seq', (SELECT MAX(id) FROM orders))")
pg_cursor.execute("SELECT setval('order_items_id_seq', (SELECT MAX(id) FROM order_items))")
pg_cursor.execute("SELECT setval('reviews_id_seq', (SELECT MAX(id) FROM reviews))")
pg_conn.commit()

pg_cursor.close()
pg_conn.close()

print("Insert MongoDB...")

client, db = get_mongo_connection()

# Clear existing data
for coll in ['categories', 'users', 'products', 'orders', 'order_items', 'reviews']:
    db[coll].delete_many({})

mongo_categories = [{'_id': c['id'], **c} for c in categories]
db.categories.insert_many(mongo_categories)

mongo_users = [{'_id': u['id'], **u} for u in users]
db.users.insert_many(mongo_users)

mongo_products = [{'_id': p['id'], **p} for p in products]
db.products.insert_many(mongo_products)

mongo_orders = [{'_id': o['id'], **o} for o in orders]
db.orders.insert_many(mongo_orders)

mongo_items = [{'_id': i['id'], **i} for i in order_items]
db.order_items.insert_many(mongo_items)

mongo_reviews = [{'_id': r['id'], **r} for r in reviews]
db.reviews.insert_many(mongo_reviews)
print("  MongoDB - gata")

client.close()

print("\nVerificare...")

# PostgreSQL 
pg_conn = get_pg_connection()
pg_cursor = pg_conn.cursor()

pg_counts = {}
for table in ['categories', 'users', 'products', 'orders', 'order_items', 'reviews']:
    pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    pg_counts[table] = pg_cursor.fetchone()[0]

pg_cursor.close()
pg_conn.close()

# MongoDB
client, db = get_mongo_connection()

mongo_counts = {}
for coll in ['categories', 'users', 'products', 'orders', 'order_items', 'reviews']:
    mongo_counts[coll] = db[coll].count_documents({})

client.close()

# Comparare
all_match = True
for table in ['categories', 'users', 'products', 'orders', 'order_items', 'reviews']:
    if pg_counts[table] != mongo_counts[table]:
        print(f"  {table}: DIFERIT!")
        all_match = False

if all_match:
    total = sum(pg_counts.values())
    print(f"  Date identice: {total} inregistrari")
    print("Gata!\n")
else:
    print("EROARE: Datele difera!")

