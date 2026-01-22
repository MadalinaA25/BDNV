#!/usr/bin/env python3
import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    get_pg_connection, get_mongo_connection,
    print_section, print_success, print_info
)

print("\n=== Script 4: Test Performanta ===")

results = {
    "test_date": datetime.now().isoformat(),
    "postgresql": {},
    "mongodb": {},
    "queries": []
}

def measure_time(func, iterations=5):
    """Execute function multiple times and return average time in ms"""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    return {
        "min": round(min(times), 3),
        "max": round(max(times), 3),
        "avg": round(sum(times) / len(times), 3),
        "result_count": result if isinstance(result, int) else len(result) if hasattr(result, '__len__') else 1
    }

print("\nPostgreSQL:")

pg_conn = get_pg_connection()
pg_cursor = pg_conn.cursor()

print("  Q1: SELECT all products")
def pg_select_all_products():
    pg_cursor.execute("SELECT * FROM products")
    return pg_cursor.fetchall()
pg_q1 = measure_time(pg_select_all_products)
print(f"     {pg_q1['avg']}ms")

print("  Q2: WHERE price > 500")
def pg_select_expensive():
    pg_cursor.execute("SELECT * FROM products WHERE price > 500")
    return pg_cursor.fetchall()
pg_q2 = measure_time(pg_select_expensive)
print(f"     {pg_q2['avg']}ms")

print("  Q3: JOIN orders-users")
def pg_join_orders_users():
    pg_cursor.execute("""
        SELECT o.order_number, u.username, u.email, o.total_amount, o.status
        FROM orders o
        JOIN users u ON o.user_id = u.id
    """)
    return pg_cursor.fetchall()
pg_q3 = measure_time(pg_join_orders_users)
print(f"     {pg_q3['avg']}ms")

print("  Q4: COUNT by status")
def pg_aggregate():
    pg_cursor.execute("""
        SELECT status, COUNT(*) as count, SUM(total_amount) as total
        FROM orders
        GROUP BY status
    """)
    return pg_cursor.fetchall()
pg_q4 = measure_time(pg_aggregate)
print(f"     {pg_q4['avg']}ms")

print("  Q5: Complex JOIN")
def pg_complex_join():
    pg_cursor.execute("""
        SELECT o.order_number, p.name as product_name, oi.quantity, oi.total_price, c.name as category
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        JOIN categories c ON p.category_id = c.id
        WHERE o.status = 'completed'
    """)
    return pg_cursor.fetchall()
pg_q5 = measure_time(pg_complex_join)
print(f"     {pg_q5['avg']}ms")

print("  Q6: LIKE search")
def pg_like_search():
    pg_cursor.execute("SELECT * FROM products WHERE name LIKE '%Pro%'")
    return pg_cursor.fetchall()
pg_q6 = measure_time(pg_like_search)
print(f"     {pg_q6['avg']}ms")

pg_cursor.close()
pg_conn.close()

results["postgresql"] = {
    "q1_select_all": pg_q1,
    "q2_select_where": pg_q2,
    "q3_join": pg_q3,
    "q4_aggregate": pg_q4,
    "q5_complex_join": pg_q5,
    "q6_like_search": pg_q6,
    "total_avg_ms": round(pg_q1['avg'] + pg_q2['avg'] + pg_q3['avg'] + pg_q4['avg'] + pg_q5['avg'] + pg_q6['avg'], 3)
}

print("\nMongoDB:")

client, db = get_mongo_connection()

print("  Q1: Find all products")
def mongo_find_all():
    return list(db.products.find())
mongo_q1 = measure_time(mongo_find_all)
print(f"     {mongo_q1['avg']}ms")

print("  Q2: price > 500")
def mongo_find_expensive():
    return list(db.products.find({"price": {"$gt": 500}}))
mongo_q2 = measure_time(mongo_find_expensive)
print(f"     {mongo_q2['avg']}ms")

print("  Q3: Lookup orders-users")
def mongo_lookup_users():
    pipeline = [
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "user"
        }},
        {"$unwind": "$user"},
        {"$project": {
            "order_number": 1,
            "username": "$user.username",
            "email": "$user.email",
            "total_amount": 1,
            "status": 1
        }}
    ]
    return list(db.orders.aggregate(pipeline))
mongo_q3 = measure_time(mongo_lookup_users)
print(f"     {mongo_q3['avg']}ms")

print("  Q4: Aggregate by status")
def mongo_aggregate():
    pipeline = [
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total": {"$sum": "$total_amount"}
        }}
    ]
    return list(db.orders.aggregate(pipeline))
mongo_q4 = measure_time(mongo_aggregate)
print(f"     {mongo_q4['avg']}ms")

print("  Q5: Complex pipeline")
def mongo_complex_pipeline():
    pipeline = [
        {"$match": {"status": "completed"}},
        {"$lookup": {
            "from": "order_items",
            "localField": "id",
            "foreignField": "order_id",
            "as": "items"
        }},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "localField": "items.product_id",
            "foreignField": "id",
            "as": "product"
        }},
        {"$unwind": "$product"},
        {"$lookup": {
            "from": "categories",
            "localField": "product.category_id",
            "foreignField": "id",
            "as": "category"
        }},
        {"$unwind": "$category"},
        {"$project": {
            "order_number": 1,
            "product_name": "$product.name",
            "quantity": "$items.quantity",
            "total_price": "$items.total_price",
            "category": "$category.name"
        }}
    ]
    return list(db.orders.aggregate(pipeline))
mongo_q5 = measure_time(mongo_complex_pipeline)
print(f"     {mongo_q5['avg']}ms")

print("  Q6: Regex search")
def mongo_regex_search():
    return list(db.products.find({"name": {"$regex": "Pro", "$options": "i"}}))
mongo_q6 = measure_time(mongo_regex_search)
print(f"     {mongo_q6['avg']}ms")

client.close()

results["mongodb"] = {
    "q1_find_all": mongo_q1,
    "q2_find_filter": mongo_q2,
    "q3_lookup": mongo_q3,
    "q4_aggregate": mongo_q4,
    "q5_complex_pipeline": mongo_q5,
    "q6_regex_search": mongo_q6,
    "total_avg_ms": round(mongo_q1['avg'] + mongo_q2['avg'] + mongo_q3['avg'] + mongo_q4['avg'] + mongo_q5['avg'] + mongo_q6['avg'], 3)
}

# Query comparison data
results["queries"] = [
    {"name": "Select All", "postgresql": pg_q1['avg'], "mongodb": mongo_q1['avg']},
    {"name": "Filter (WHERE)", "postgresql": pg_q2['avg'], "mongodb": mongo_q2['avg']},
    {"name": "JOIN/Lookup", "postgresql": pg_q3['avg'], "mongodb": mongo_q3['avg']},
    {"name": "Aggregation", "postgresql": pg_q4['avg'], "mongodb": mongo_q4['avg']},
    {"name": "Complex JOIN", "postgresql": pg_q5['avg'], "mongodb": mongo_q5['avg']},
    {"name": "Text Search", "postgresql": pg_q6['avg'], "mongodb": mongo_q6['avg']},
]

print("\nRezultat:")
print(f"  PostgreSQL: {results['postgresql']['total_avg_ms']}ms")
print(f"  MongoDB: {results['mongodb']['total_avg_ms']}ms")

if results['postgresql']['total_avg_ms'] < results['mongodb']['total_avg_ms']:
    diff = results['mongodb']['total_avg_ms'] / results['postgresql']['total_avg_ms']
    print(f"  PostgreSQL e {diff:.2f}x mai rapid")
else:
    diff = results['postgresql']['total_avg_ms'] / results['mongodb']['total_avg_ms']
    print(f"  MongoDB e {diff:.2f}x mai rapid")

os.makedirs("results", exist_ok=True)
with open("results/performance_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("Gata!\n")
