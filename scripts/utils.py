import os
import time
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pg8000
from pymongo import MongoClient
from faker import Faker

load_dotenv()

# Configuration
PG_HOST = os.getenv('PG_HOST', 'localhost')
PG_PORT = int(os.getenv('PG_PORT', 5432))
PG_USER = os.getenv('PG_USER', 'postgres')
PG_PASSWORD = os.getenv('PG_PASSWORD')
PG_DATABASE = os.getenv('PG_DATABASE', 'comparison_db')

MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB = os.getenv('MONGO_DB', 'comparison_db')

fake = Faker()
Faker.seed(42)  
random.seed(42)
# PostgreSQL Functions

def get_pg_connection(database=None):
    """Get PostgreSQL connection"""
    return pg8000.connect(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASSWORD,
        database=database or PG_DATABASE
    )

def test_pg_connection():
    """Test PostgreSQL connection"""
    try:
        conn = get_pg_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return True, version
    except Exception as e:
        return False, str(e)


# MongoDB Functions
def get_mongo_connection():
    """Get MongoDB connection"""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB]
    return client, db

def test_mongo_connection():
    """Test MongoDB connection"""
    try:
        client, db = get_mongo_connection()
        client.admin.command('ping')
        info = client.server_info()
        client.close()
        return True, info.get('version', 'unknown')
    except Exception as e:
        return False, str(e)

# Data Generation - IDENTICE pentru ambele baze

def generate_categories():
    """Generate categories - IDENTICE"""
    return [
        {'id': 1, 'name': 'Electronics', 'description': 'Electronic devices and gadgets'},
        {'id': 2, 'name': 'Clothing', 'description': 'Fashion and apparel'},
        {'id': 3, 'name': 'Books', 'description': 'Books and publications'},
        {'id': 4, 'name': 'Home & Garden', 'description': 'Home improvement and garden'},
        {'id': 5, 'name': 'Sports', 'description': 'Sports equipment and accessories'},
        {'id': 6, 'name': 'Toys', 'description': 'Toys and games for all ages'},
        {'id': 7, 'name': 'Beauty', 'description': 'Beauty and personal care'},
        {'id': 8, 'name': 'Food', 'description': 'Food and beverages'},
    ]

def generate_users(count=100):
    """Generate users - IDENTICE"""
    Faker.seed(42)
    random.seed(42)
    users = []
    for i in range(1, count + 1):
        users.append({
            'id': i,
            'username': f"user_{i:04d}",
            'email': f"user{i}@example.com",
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'phone': fake.phone_number()[:15],
            'address': fake.street_address()[:100],
            'city': fake.city()[:50],
            'country': fake.country()[:50],
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365))
        })
    return users

def generate_products(count=200):
    """Generate products - IDENTICE"""
    Faker.seed(42)
    random.seed(42)
    products = []
    for i in range(1, count + 1):
        products.append({
            'id': i,
            'sku': f"SKU-{i:06d}",
            'name': fake.catch_phrase()[:100],
            'description': fake.text(max_nb_chars=200),
            'category_id': random.randint(1, 8),
            'price': round(random.uniform(9.99, 499.99), 2),
            'stock_quantity': random.randint(0, 500),
            'rating': round(random.uniform(1.0, 5.0), 2),
            'review_count': random.randint(0, 200),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 365))
        })
    return products

def generate_orders(users, count=150):
    """Generate orders - IDENTICE"""
    Faker.seed(42)
    random.seed(42)
    orders = []
    statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    payment_methods = ['credit_card', 'debit_card', 'paypal', 'bank_transfer']
    
    for i in range(1, count + 1):
        user = random.choice(users)
        orders.append({
            'id': i,
            'order_number': f"ORD-{i:08d}",
            'user_id': user['id'],
            'status': random.choice(statuses),
            'total_amount': round(random.uniform(25.00, 500.00), 2),
            'shipping_address': fake.street_address()[:100],
            'shipping_city': fake.city()[:50],
            'shipping_country': fake.country()[:50],
            'payment_method': random.choice(payment_methods),
            'payment_status': random.choice(['pending', 'paid', 'refunded']),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 90))
        })
    return orders

def generate_order_items(orders, products):
    """Generate order items - IDENTICE"""
    random.seed(42)
    items = []
    item_id = 1
    
    for order in orders:
        num_items = random.randint(1, 4)
        for _ in range(num_items):
            product = random.choice(products)
            qty = random.randint(1, 3)
            items.append({
                'id': item_id,
                'order_id': order['id'],
                'product_id': product['id'],
                'quantity': qty,
                'unit_price': product['price'],
                'total_price': round(qty * product['price'], 2)
            })
            item_id += 1
    return items

def generate_reviews(users, products, count=80):
    """Generate reviews - IDENTICE"""
    Faker.seed(42)
    random.seed(42)
    reviews = []
    
    for i in range(1, count + 1):
        reviews.append({
            'id': i,
            'product_id': random.choice(products)['id'],
            'user_id': random.choice(users)['id'],
            'rating': random.randint(1, 5),
            'title': fake.sentence(nb_words=5)[:100],
            'comment': fake.text(max_nb_chars=200),
            'is_verified': random.choice([True, False]),
            'created_at': datetime.now() - timedelta(days=random.randint(1, 60))
        })
    return reviews

# Utility Functions

def measure_time(func):
    """Measure execution time in milliseconds"""
    start = time.time()
    result = func()
    elapsed = (time.time() - start) * 1000
    return result, elapsed

def print_section(title):
    print(f"\n--- {title} ---")

def print_success(msg):
    print(f"  OK: {msg}")

def print_error(msg):
    print(f"  EROARE: {msg}")

def print_info(msg):
    print(f"  {msg}")
