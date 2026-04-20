"""
test_load_scripts.py — Validate the Python load patterns from 4-load.md
against localhost:7687 / jtbd database. Cleans up after each test.
"""
import os, sys
import pandas as pd
from neo4j import GraphDatabase

URI  = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
DB   = "jtbd"

driver = GraphDatabase.driver(URI, auth=AUTH)

def cleanup():
    with driver.session(database=DB) as s:
        s.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS").consume()

def count_nodes():
    records, _, _ = driver.execute_query(
        "MATCH (n) RETURN labels(n)[0] AS l, count(n) AS c ORDER BY c DESC",
        database_=DB
    )
    return {r["l"]: r["c"] for r in records}

# ─────────────────────────────────────────────────────────────
# Test 1: Preferred batch loading pattern (Northwind)
# ─────────────────────────────────────────────────────────────
print("\n=== Test 1: Batch loading via DataFrame (Northwind) ===")
cleanup()

BATCH = 500

def load_batches(query: str, rows: list[dict]) -> int:
    total = 0
    for i in range(0, len(rows), BATCH):
        records, summary, _ = driver.execute_query(query, rows=rows[i:i+BATCH], database_=DB)
        total += summary.counters.nodes_created + summary.counters.relationships_created
    return total

products   = pd.read_csv("https://data.neo4j.com/northwind/products.csv")
categories = pd.read_csv("https://data.neo4j.com/northwind/categories.csv")

n = load_batches("""
    UNWIND $rows AS row
    MERGE (p:Product {productID: row.productID})
    SET p.productName  = row.productName,
        p.unitPrice    = toFloat(row.unitPrice),
        p.unitsInStock = toInteger(row.unitsInStock)
""", products.to_dict("records"))
print(f"  Products created: {n}")

n = load_batches("""
    UNWIND $rows AS row
    MERGE (c:Category {categoryID: row.categoryID})
    SET c.categoryName = row.categoryName,
        c.description  = row.description
""", categories.to_dict("records"))
print(f"  Categories created: {n}")

n = load_batches("""
    UNWIND $rows AS row
    MATCH (p:Product  {productID:  row.productID})
    MATCH (c:Category {categoryID: row.categoryID})
    MERGE (p)-[:PART_OF]->(c)
""", products.to_dict("records"))
print(f"  PART_OF rels created: {n}")

counts = count_nodes()
print(f"  Node counts: {counts}")
assert counts.get("Product", 0) > 0, "No Product nodes"
assert counts.get("Category", 0) > 0, "No Category nodes"
print("  PASS")

# ─────────────────────────────────────────────────────────────
# Test 2: Synthetic data (Path B)
# ─────────────────────────────────────────────────────────────
print("\n=== Test 2: Synthetic data (Path B) ===")
cleanup()

with driver.session(database=DB) as s:
    s.run("""CYPHER 25
        UNWIND range(1, 200) AS i
        MERGE (p:Person {id: toString(i)})
        SET p.name = 'Person ' + toString(i),
            p.email = 'person' + toString(i) + '@example.com',
            p.createdAt = datetime() - duration({days: toInteger(rand() * 365)})
    """)
    s.run("""CYPHER 25
        MATCH (a:Person), (b:Person)
        WHERE a.id < b.id AND rand() < 0.05
        MERGE (a)-[:FOLLOWS]->(b)
    """)

counts = count_nodes()
print(f"  Node counts: {counts}")
records, _, _ = driver.execute_query(
    "MATCH ()-[r:FOLLOWS]->() RETURN count(r) AS c", database_=DB
)
rels = records[0]["c"]
print(f"  FOLLOWS rels: {rels}")
assert counts.get("Person", 0) == 200, f"Expected 200 Person nodes, got {counts.get('Person',0)}"
assert rels > 0, "No FOLLOWS relationships created"
print("  PASS")

# ─────────────────────────────────────────────────────────────
cleanup()
driver.close()
print("\nAll load script tests passed.")
