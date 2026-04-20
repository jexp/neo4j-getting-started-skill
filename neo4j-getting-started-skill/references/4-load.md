# Stage 4 — load
# Import data into the database. Always apply schema constraints first.

## Step L0 — Apply schema constraints (always, before any data)

```bash
source .env
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" --file schema.cypher
```

Or via Python if cypher-shell unavailable:
```python
from neo4j import GraphDatabase; import os
driver = GraphDatabase.driver(os.environ["NEO4J_URI"],
                               auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]))
with driver.session() as s:
    for stmt in open("schema.cypher").read().split(";"):
        stmt = stmt.strip()
        if stmt and not stmt.startswith("//"):
            s.run(stmt)
driver.close()
print("Schema applied")
```

## Import rules (apply to all paths)

- **MERGE nodes first** — complete all node MERGE statements before any relationship MERGE
- **MERGE relationships second** — only after all endpoint node types are loaded
- **Batch size**: 500 rows per call — pass as `$rows` parameter list from Python
- **Use MERGE not CREATE** — idempotent, safe to re-run
- **All scripts go in `import/`** — user can re-run them for updates

## Preferred pattern — Python batch loading via DataFrame

Load data into a pandas DataFrame first, then push rows to Neo4j in batches using
`driver.execute_query(..., rows=batch)`. This works with **any data source and any
database target** — local files, HTTPS, S3/GCS, Parquet, relational DBs, MongoDB, etc.
No Neo4j import directory access required (works on Aura out of the box).

```python
import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)

BATCH = 500

def load_batches(query: str, rows: list[dict]) -> int:
    total = 0
    for i in range(0, len(rows), BATCH):
        records, summary, _ = driver.execute_query(query, rows=rows[i:i+BATCH])
        total += summary.counters.nodes_created + summary.counters.relationships_created
    return total

# ── Read data — swap in any pandas-compatible source ──────────────────────────
# CSV (local or HTTPS):   pd.read_csv("https://data.neo4j.com/northwind/products.csv")
# Parquet / S3:           pd.read_parquet("s3://bucket/file.parquet")
# Relational (SQLAlchemy):pd.read_sql("SELECT * FROM products", engine)
# MongoDB:                pd.DataFrame(collection.find())

products   = pd.read_csv("https://data.neo4j.com/northwind/products.csv")
categories = pd.read_csv("https://data.neo4j.com/northwind/categories.csv")

# ── Phase 1: all node types (MERGE nodes before relationships) ─────────────────
n = load_batches("""
    UNWIND $rows AS row
    MERGE (p:Product {productID: row.productID})
    SET p.productName  = row.productName,
        p.unitPrice    = toFloat(row.unitPrice),
        p.unitsInStock = toInteger(row.unitsInStock)
""", products.to_dict("records"))
print(f"Products: {n}")

n = load_batches("""
    UNWIND $rows AS row
    MERGE (c:Category {categoryID: row.categoryID})
    SET c.categoryName = row.categoryName,
        c.description  = row.description
""", categories.to_dict("records"))
print(f"Categories: {n}")

# ── Phase 2: relationships (after all nodes exist) ─────────────────────────────
n = load_batches("""
    UNWIND $rows AS row
    MATCH (p:Product  {productID:  row.productID})
    MATCH (c:Category {categoryID: row.categoryID})
    MERGE (p)-[:PART_OF]->(c)
""", products.to_dict("records"))
print(f"PART_OF rels: {n}")

driver.close()
```

Run: `python3 import/import.py`

### Type coercion in Cypher vs Python

Prefer coercing types in Python before passing rows (faster, avoids Cypher `toFloat()`):
```python
products["unitPrice"]    = pd.to_numeric(products["unitPrice"],    errors="coerce")
products["unitsInStock"] = pd.to_numeric(products["unitsInStock"], errors="coerce").astype("Int64")
```
Then use `row.unitPrice` directly in Cypher without wrapping functions.

---

## Path A — Demo dataset

```bash
source .env
# Movies
curl -s https://raw.githubusercontent.com/neo4j-graph-examples/movies/main/data/movies.cypher \
  | cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD"
```

For other demos, fetch the import URL from https://github.com/neo4j-graph-examples.

## Path B — Synthetic data

Generate `import/generate.py` — nodes first, then relationships:

```python
from neo4j import GraphDatabase
import os, random

driver = GraphDatabase.driver(os.environ["NEO4J_URI"],
                               auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"]))

with driver.session() as s:
    # Step 1: MERGE all nodes first
    s.run("""CYPHER 25
        UNWIND range(1, 200) AS i
        MERGE (p:Person {id: toString(i)})
        SET p.name = 'Person ' + toString(i),
            p.email = 'person' + toString(i) + '@example.com',
            p.createdAt = datetime() - duration({days: toInteger(rand() * 365)})
    """)

    # Step 2: MERGE relationships second (after all nodes exist)
    s.run("""CYPHER 25
        MATCH (a:Person), (b:Person)
        WHERE a.id < b.id AND rand() < 0.05
        MERGE (a)-[:FOLLOWS]->(b)
    """)

records, _, _ = driver.execute_query("MATCH (n) RETURN labels(n)[0] AS l, count(n) AS c")
for r in records:
    print(f"  {r['l']}: {r['c']}")
driver.close()
```

Run: `python3 import/generate.py`

## Path C — CSV / tabular data (any source)

Use the **Python batch loading pattern** above. Install dependencies first:
```bash
pip install neo4j neo4j-rust-ext pandas
```

Adapt the DataFrame source to match:

| Source | pandas call |
|--------|-------------|
| Local CSV | `pd.read_csv("./data/file.csv")` |
| HTTPS CSV | `pd.read_csv("https://…/file.csv")` |
| Parquet / S3 | `pd.read_parquet("s3://bucket/file.parquet")` |
| PostgreSQL | `pd.read_sql("SELECT * FROM table", engine)` |
| MongoDB | `pd.DataFrame(collection.find({}, {"_id": 0}))` |
| Excel | `pd.read_excel("file.xlsx")` |

Always follow **Phase 1 (all nodes) → Phase 2 (all relationships)** regardless of source.

## Path D — Document / GraphRAG pipeline

Read and follow `${CLAUDE_SKILL_DIR}/references/capabilities/kg-from-documents.md` for the full pipeline.
Summary:

```python
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.embeddings import OpenAIEmbeddings  # or Cohere, Ollama, etc.

embedder = OpenAIEmbeddings(model=EMBEDDING_MODEL)
pipeline = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    embedder=embedder,
    entities=["Person", "Organization", "Topic"],  # adapt to domain
    relations=["MENTIONS", "RELATED_TO"],
)
for text in load_documents("./data/docs/"):
    await pipeline.run_async(text=text)
```

After ingestion, create vector and fulltext indexes (from schema.cypher).

## Step L5 — Post-import search indexes

```cypher
CYPHER 25
CREATE FULLTEXT INDEX <label>_name IF NOT EXISTS
  FOR (n:<Label>) ON EACH [n.name];
```

## Step L6 — Write reset.cypher (always)

```bash
cat > reset.cypher << 'EOF'
// Delete all data — keeps schema (constraints + indexes)
CYPHER 25
MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS;
EOF
echo "Reset script: cypher-shell ... --file reset.cypher"
```

## Step L7 — HITL data preview pause

Show row counts and a sample before proceeding:
```bash
source .env
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" \
  "CYPHER 25 MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC"
```

In autonomous mode: log counts and continue.

## Completion condition

- `MATCH (n) RETURN count(n)` ≥ 50
- Each node label has ≥1 node
- `import/` directory contains the script(s) used
- `reset.cypher` exists

## On Completion — write to progress.md

Record node counts per label and total relationships:
```markdown
### 4-load
status: done
nodes=<e.g. "200 Person, 50 Post">
relationships=<e.g. "1400 FOLLOWS, 300 POSTED">
```

## Error recovery

- Import partially failed → run `reset.cypher`, re-apply `schema.cypher`, retry from scratch
- MERGE slow → check constraint was created before import (Step L0)
- DataFrame empty → verify source URL/path and column names match schema.json
