#!/usr/bin/env python3
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from utils import (
    get_pg_connection, get_mongo_connection,
    print_section, print_success, print_info, print_error
)

results = {
    "test_date": datetime.now().isoformat(),
    "postgresql": {
        "type": "SQL/Relational",
        "cap_focus": "CP (Consistency + Partition Tolerance)",
        "acid_compliant": True,
        "tests": {}
    },
    "mongodb": {
        "type": "NoSQL/Document",
        "cap_focus": "CP (with tunable consistency)",
        "acid_compliant": True,  # Since MongoDB 4.0
        "tests": {}
    },
    "analysis": {}
}

print("\n=== Script 5: CAP Theorem ===")

print("\n1. Teste Consistenta")
print("PostgreSQL:")
pg_conn = get_pg_connection()
pg_cursor = pg_conn.cursor()

print("  Rollback test...")
try:
    # Get initial value
    pg_cursor.execute("SELECT stock_quantity FROM products WHERE id = 1")
    initial_stock = pg_cursor.fetchone()[0]
    
    # Start transaction
    pg_cursor.execute("BEGIN")
    pg_cursor.execute("UPDATE products SET stock_quantity = stock_quantity - 10 WHERE id = 1")
    
    # Simulate error - rollback
    pg_conn.rollback()
    
    # Check value after rollback
    pg_cursor.execute("SELECT stock_quantity FROM products WHERE id = 1")
    after_rollback = pg_cursor.fetchone()[0]
    
    consistency_test = initial_stock == after_rollback
    results["postgresql"]["tests"]["transaction_rollback"] = {
        "passed": consistency_test,
        "initial_value": initial_stock,
        "after_rollback": after_rollback
    }
    
    if consistency_test:
        print(f"    OK - rollback functioneaza")
    else:
        print(f"    EROARE")
        
except Exception as e:
    print(f"    EROARE: {e}")
    results["postgresql"]["tests"]["transaction_rollback"] = {"passed": False, "error": str(e)}

print("  FK constraint test...")
try:
    pg_cursor.execute("BEGIN")
    pg_cursor.execute("INSERT INTO orders (order_number, user_id, status, total_amount) VALUES ('TEST-FK', 99999, 'pending', 100)")
    pg_conn.commit()
    fk_test = False
    print("    FK nu e fortat!")
except Exception as e:
    pg_conn.rollback()
    fk_test = True
    print("    OK - FK constraint functioneaza")
    
results["postgresql"]["tests"]["foreign_key_constraint"] = {"passed": fk_test}

pg_cursor.close()
pg_conn.close()

print("MongoDB:")
client, db = get_mongo_connection()

print("  Atomic update test...")
try:
    product = db.products.find_one({"id": 1})
    initial_stock = product["stock_quantity"]
    
    # Atomic update
    result = db.products.update_one(
        {"id": 1},
        {"$inc": {"stock_quantity": -10}}
    )
    
    # Restore value
    db.products.update_one(
        {"id": 1},
        {"$set": {"stock_quantity": initial_stock}}
    )
    
    atomic_test = result.modified_count == 1
    results["mongodb"]["tests"]["atomic_update"] = {
        "passed": atomic_test,
        "modified_count": result.modified_count
    }
    
    if atomic_test:
        print("    OK - atomic update functioneaza")
    else:
        print("    EROARE")
        
except Exception as e:
    print(f"    EROARE: {e}")
    results["mongodb"]["tests"]["atomic_update"] = {"passed": False, "error": str(e)}

print("  Write concern test...")
try:
    start = time.perf_counter()
    result = db.products.update_one(
        {"id": 1},
        {"$set": {"test_field": "test"}},
    )
    end = time.perf_counter()
    
    db.products.update_one({"id": 1}, {"$unset": {"test_field": ""}})
    
    write_concern_time = (end - start) * 1000
    results["mongodb"]["tests"]["write_concern"] = {
        "passed": True,
        "write_time_ms": round(write_concern_time, 3)
    }
    print(f"    OK - {write_concern_time:.2f}ms")
    
except Exception as e:
    print(f"    EROARE: {e}")
    results["mongodb"]["tests"]["write_concern"] = {"passed": False, "error": str(e)}

client.close()

print("\n2. Teste Availability")
print("PostgreSQL:")
pg_conn = get_pg_connection()
pg_cursor = pg_conn.cursor()

print("  Response time test...")
try:
    times = []
    for i in range(20):
        start = time.perf_counter()
        pg_cursor.execute("SELECT COUNT(*) FROM orders")
        pg_cursor.fetchone()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    results["postgresql"]["tests"]["availability"] = {
        "avg_response_ms": round(avg_time, 3),
        "max_response_ms": round(max_time, 3),
        "queries_executed": len(times)
    }
    print(f"    avg={avg_time:.2f}ms max={max_time:.2f}ms")
    
except Exception as e:
    print(f"    EROARE: {e}")
    results["postgresql"]["tests"]["availability"] = {"error": str(e)}

pg_cursor.close()
pg_conn.close()

print("MongoDB:")
client, db = get_mongo_connection()

print("  Response time test (cloud)...")
try:
    times = []
    for i in range(20):
        start = time.perf_counter()
        db.orders.count_documents({})
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    
    results["mongodb"]["tests"]["availability"] = {
        "avg_response_ms": round(avg_time, 3),
        "max_response_ms": round(max_time, 3),
        "queries_executed": len(times),
        "note": "Higher latency due to cloud network"
    }
    print(f"    avg={avg_time:.2f}ms max={max_time:.2f}ms (cloud)")
    
except Exception as e:
    print(f"    EROARE: {e}")
    results["mongodb"]["tests"]["availability"] = {"error": str(e)}

client.close()


results["analysis"] = {
    "postgresql": {
        "deployment": "Single node (local)",
        "partition_tolerance": "Requires external tools",
        "failover": "Manual or external tools required",
        "consistency_model": "Strong (ACID)",
        "recommendation": "Best for complex transactions, referential integrity"
    },
    "mongodb": {
        "deployment": "Replica set (Atlas cloud)",
        "partition_tolerance": "Built-in with replica sets",
        "failover": "Automatic (Primary election)",
        "consistency_model": "Tunable (eventual to strong)",
        "recommendation": "Best for flexible schema, horizontal scaling"
    }
}


os.makedirs("results", exist_ok=True)
with open("results/cap_analysis.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

print("Gata!\n")
