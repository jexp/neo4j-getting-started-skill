# Stage 7 — build
# Generate a runnable application, dashboard, or agent integration.
# v1: Python only. JavaScript in phase 2.

## Always include in requirements.txt

```
neo4j-rust-ext>=0.0.1
python-dotenv>=1.0.0
```

## Path selection

```
APP_TYPE=notebook      → Path A: Jupyter notebook
APP_TYPE=streamlit     → Path B: Streamlit dashboard
APP_TYPE=fastapi       → Path C: FastAPI backend
APP_TYPE=graphrag      → Path D: GraphRAG pipeline
APP_TYPE=explore-only  → skip build; output queries.cypher + README only
APP_TYPE=mcp           → Path E: neo4j-mcp configuration
```

## Path A — Jupyter Notebook

Generate `notebook.ipynb`. Required cells:

1. **Setup** — imports + `.env` loading via `python-dotenv`
2. **Connection** — create driver, verify connectivity
3. **Schema** — `CALL db.labels()` etc., display as DataFrame
4. **Per-query cells** — one cell per query from `queries.cypher`, display as DataFrame
5. **Graph visualization** — yfiles or pyvis (see `${CLAUDE_SKILL_DIR}/references/5-explore.md`)
6. **Use-case answer cell** — must return non-empty results + include assertion

```python
# Cell: Connection
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os, pandas as pd

load_dotenv()
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)
driver.verify_connectivity()
print("✓ Connected")

def run_query(q, params={}):
    records, _, _ = driver.execute_query(q, parameters_=params,
                                          database_=os.environ.get("NEO4J_DATABASE","neo4j"))
    return pd.DataFrame([r.data() for r in records])
```

```python
# Cell: Use-case answer (adapt to domain)
df = run_query("""
    CYPHER 25
    MATCH (me:Person {id: $id})-[:FOLLOWS]->(f)-[:FOLLOWS]->(fof)
    WHERE NOT (me)-[:FOLLOWS]->(fof) AND me <> fof
    RETURN fof.name AS recommendation, count(f) AS mutual
    ORDER BY mutual DESC LIMIT 10
""", {"id": "1"})
assert len(df) > 0, "No recommendations — check import and traversal query"
df.plot(kind='barh', x='recommendation', y='mutual', title='Recommendations')
```

Validate: `python -m json.tool notebook.ipynb > /dev/null && echo "✓ Valid notebook"`

Add to `requirements.txt`:
```
jupyter>=1.0.0
pandas>=2.0.0
matplotlib>=3.0.0
yfiles-jupyter-graphs-for-neo4j>=1.0.0
```

## Path B — Streamlit Dashboard

Generate `app.py`:

```python
import streamlit as st
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os, pandas as pd

load_dotenv()

@st.cache_resource
def get_driver():
    return GraphDatabase.driver(
        os.environ["NEO4J_URI"],
        auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    )

def run_query(q, params={}):
    driver = get_driver()
    records, _, _ = driver.execute_query(q, parameters_=params,
                                          database_=os.environ.get("NEO4J_DATABASE","neo4j"))
    return pd.DataFrame([r.data() for r in records])

st.title(f"{DOMAIN} — {USE_CASE}")

# Sidebar controls
limit = st.sidebar.slider("Results limit", 5, 100, 20)

# Section 1: Overview
st.header("Database Overview")
df = run_query("CYPHER 25 MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count")
st.bar_chart(df.set_index("label"))

# Section 2: Use-case answer (adapt to domain)
st.header("<Use-case headline>")
df2 = run_query("<traversal query from queries.cypher>", {"limit": limit})
st.dataframe(df2)
assert not df2.empty, "Query returned no results"
```

Run: `streamlit run app.py`
Validate: `python -m py_compile app.py && echo "✓ Syntax OK"`

## Path C — FastAPI Backend

Generate `main.py`:

```python
from fastapi import FastAPI
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI(title=f"{DOMAIN} API — {USE_CASE}")
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)

@app.get("/health")
def health():
    driver.verify_connectivity()
    records, _, _ = driver.execute_query("MATCH (n) RETURN count(n) AS total")
    return {"status": "ok", "total_nodes": records[0]["total"]}

@app.get("/<entities>")
def list_entities(limit: int = 20):
    records, _, _ = driver.execute_query(
        "CYPHER 25 MATCH (n:<Label>) RETURN n.id AS id, n.name AS name LIMIT $limit",
        limit_=limit, database_=os.environ.get("NEO4J_DATABASE","neo4j")
    )
    return [dict(r) for r in records]

@app.get("/<entities>/{id}/recommendations")
def recommendations(id: str, limit: int = 10):
    records, _, _ = driver.execute_query(
        "<traversal query from queries.cypher>",
        id=id, limit_=limit,
        database_=os.environ.get("NEO4J_DATABASE","neo4j")
    )
    result = [dict(r) for r in records]
    assert len(result) > 0 or True  # empty is valid if entity has no connections
    return result
```

Validate: `python -m py_compile main.py && echo "✓ Syntax OK"`
Run: `uvicorn main:app --reload`
Docs: `http://localhost:8000/docs`

## Path D — GraphRAG Pipeline

Generate `graphrag_app.py`:

```python
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings import OpenAIEmbeddings  # swap for Cohere/Ollama
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)
embedder = OpenAIEmbeddings(model=os.environ.get("EMBEDDING_MODEL","text-embedding-3-small"))

retrieval_query = """
MATCH (node)<-[:HAS_CHUNK]-(doc:Document)
OPTIONAL MATCH (node)-[:MENTIONS]->(e:Entity)
RETURN node.text AS chunk_text, doc.title AS source,
       collect(DISTINCT e.name) AS entities, score
ORDER BY score DESC
"""

retriever = HybridCypherRetriever(
    driver=driver,
    vector_index_name="chunk_embeddings",
    fulltext_index_name="entity_search",
    retrieval_query=retrieval_query,
    embedder=embedder,
)

rag = GraphRAG(retriever=retriever, llm=llm)

if __name__ == "__main__":
    query = f"Tell me about {USE_CASE}"
    response = rag.search(query_text=query, retriever_config={"top_k": 5})
    assert response.answer, "GraphRAG returned empty — check embeddings and vector index"
    print(response.answer)
```

Add to `requirements.txt`:
```
neo4j-graphrag>=1.13.0
openai>=1.0.0
```

## Path E — MCP Integration

Install `neo4j-mcp` binary (done in `prerequisites`). Write config files:

**For Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS,
`%APPDATA%\Claude\claude_desktop_config.json` on Windows):
```json
{
  "mcpServers": {
    "neo4j": {
      "command": "/absolute/path/to/neo4j-mcp",
      "env": {
        "NEO4J_URI": "<from .env>",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "<from .env>",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

**For Claude Code** (`.claude/settings.json` in project root):
```json
{
  "mcpServers": {
    "neo4j": {
      "command": "./neo4j-mcp",
      "env": {
        "NEO4J_URI": "<from .env>",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "<from .env>",
        "NEO4J_DATABASE": "neo4j"
      }
    }
  }
}
```

Available MCP tools after restart: `read-cypher`, `write-cypher`, `get-schema`, `list-gds-procedures`.

Tell user: "Restart Claude Desktop or Claude Code. The `neo4j` server will appear as available tools."

For read-only mode (recommended for production/shared DBs), add:
```json
"NEO4J_READ_ONLY": "true"
```

## On Completion — write to progress.md

```markdown
### 7-build
status: done
artifact=<filename, e.g. notebook.ipynb or app.py>
app_type=<notebook|streamlit|fastapi|graphrag|mcp>
run_command=<e.g. "jupyter notebook notebook.ipynb" or "streamlit run app.py">
```

## Completion condition

- At least one artifact exists and passes syntax check (or is valid JSON for notebooks)
- At least one cell / endpoint / function returns non-empty results for the use-case query
- `requirements.txt` written
- MCP config written to correct location (if `APP_TYPE=mcp` or requested)

## Error recovery

- App returns empty results → verify `load` stage completed, check query parameter names match schema
- Import error → check `requirements.txt`, run `pip install -r requirements.txt`
- MCP not appearing in Claude → verify absolute path to binary, restart the app
