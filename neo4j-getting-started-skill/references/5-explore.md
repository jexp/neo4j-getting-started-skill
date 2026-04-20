# Stage 5 — explore
# Give the user a visual view of their graph — the "it clicks" moment.
# This is a hard success gate. Do not skip.

## Why this matters

For first-time Neo4j users, seeing nodes and edges rendered is often the defining moment when graph databases make sense. Always deliver a visual entry point after import.

## Option A — Neo4j Browser standalone (always available, zero install)

Generate and print the URL:

```python
import os, urllib.parse
from dotenv import load_dotenv
load_dotenv()

uri = os.environ.get("NEO4J_URI", "")
user = os.environ.get("NEO4J_USERNAME", "neo4j")

# Strip scheme prefix to get host
host = uri
for prefix in ["neo4j+s://", "neo4j://", "bolt+s://", "bolt://"]:
    host = host.replace(prefix, "")

# Encode the connectURL parameter
connect_url = f"neo4j+s://{user}@{host}"
encoded = urllib.parse.quote(connect_url, safe="")
browser_url = f"https://browser.neo4j.io/?connectURL={encoded}"

print(f"\n🔍 See your graph:")
print(f"   {browser_url}")
print(f"\n   Run this query after connecting:")
print(f"   MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 50")
```

Tell the user: "Open the URL above, connect with your password from `.env`, then run the query to see your data as a graph."

## Option B — Notebook visualization (for APP_TYPE=notebook)

Add a visualization cell using yfiles (recommended) or pyvis:

```python
# Option B1: yfiles-jupyter-graphs-for-neo4j (best visual quality)
# pip install yfiles-jupyter-graphs-for-neo4j
from yfiles_jupyter_graphs_for_neo4j import Neo4jGraphWidget
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)
w = Neo4jGraphWidget(driver)
w.show_cypher("CYPHER 25 MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 50")
w  # display in notebook
```

```python
# Option B2: pyvis (lightweight, no extra neo4j dep)
# pip install pyvis
from pyvis.network import Network
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
load_dotenv()

driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)
records, _, _ = driver.execute_query(
    "CYPHER 25 MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50"
)

net = Network(height="600px", notebook=True)
for record in records:
    n, m = record["n"], record["m"]
    net.add_node(n.element_id, label=list(n.labels)[0], title=str(dict(n)))
    net.add_node(m.element_id, label=list(m.labels)[0], title=str(dict(m)))
    net.add_edge(n.element_id, m.element_id, label=record["r"].type)

net.show("graph.html")
```

## Option C — VS Code Neo4j extension

Tell the user: "If you're in VS Code, install the **Neo4j extension** — it connects to your DB and renders Cypher query results as an interactive graph directly in the editor."

## Sample visualization queries by domain

Include one of these in the browser suggestion, adapted to the user's schema:

```cypher
// Social: show follow network
CYPHER 25
MATCH (p:Person)-[:FOLLOWS]->(friend:Person)
RETURN p, friend LIMIT 50;

// E-commerce: show customer orders and products
CYPHER 25
MATCH (c:Customer)-[:PLACED]->(o:Order)-[:CONTAINS]->(p:Product)
RETURN c, o, p LIMIT 50;

// Finance: show transaction network
CYPHER 25
MATCH (a:Account)-[t:TRANSFERRED_TO]->(b:Account)
RETURN a, t, b LIMIT 50;

// KG/RAG: show document-chunk-entity structure
CYPHER 25
MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)-[:MENTIONS]->(e:Entity)
RETURN d, c, e LIMIT 50;
```

## On Completion — write to progress.md

```markdown
### 5-explore
status: done
browser_url=<the generated https://browser.neo4j.io/... URL>
viz_method=<browser|notebook-yfiles|notebook-pyvis|vscode>
```

## Completion condition

- Browser URL printed to stdout (Option A), OR
- Notebook visualization cell added (Option B), OR
- VS Code extension suggested with connection details (Option C)

At least Option A must always be delivered regardless of APP_TYPE.
