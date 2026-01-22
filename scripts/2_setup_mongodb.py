#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from utils import get_mongo_connection, test_mongo_connection, print_section, print_success, print_error

print("\n=== Script 2: MongoDB ===")
print("Conectare...")
success, result = test_mongo_connection()
if success:
    print("  Conectat la Atlas")
else:
    print(f"  Eroare: {result}")
    exit(1)

# Connect
client, db = get_mongo_connection()

# Sterg colectiile existente
print("Stergere colectii vechi...")
for coll in db.list_collection_names():
    db.drop_collection(coll)

# Creare colectii
print("Creare colectii...")

collections = ['categories', 'users', 'products', 'orders', 'order_items', 'reviews']

for coll in collections:
    db.create_collection(coll)
    print(f"  {coll} - ok")

# Indexi
print("Creare indexi...")

# Categories
db.categories.create_index("name", unique=True)

# Users
db.users.create_index("username", unique=True)
db.users.create_index("email", unique=True)

# Products
db.products.create_index("sku", unique=True)
db.products.create_index("category_id")
db.products.create_index("price")

# Orders
db.orders.create_index("order_number", unique=True)
db.orders.create_index("user_id")
db.orders.create_index("status")

# Order Items
db.order_items.create_index("order_id")
db.order_items.create_index("product_id")

# Reviews
db.reviews.create_index("product_id")
db.reviews.create_index("user_id")

print("  Indexi creati")

# Verificare
print("Verificare...")
collections = db.list_collection_names()
print(f"  {len(collections)} colectii create")

client.close()

print("Gata!\n")
