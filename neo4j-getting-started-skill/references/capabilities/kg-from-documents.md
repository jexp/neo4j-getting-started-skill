# Capability — kg-from-documents
# Build a knowledge graph from unstructured documents using neo4j-graphrag SimpleKGPipeline.
# Used in the `load` stage when DATA_SOURCE=documents.

## Overview

The `neo4j-graphrag` library's `SimpleKGPipeline` handles the full ETL from raw text to a
graph of entities and relationships, with embeddings for vector search. It requires:
- An LLM for entity/relation extraction
- An embedder for chunk embeddings
- A running Neo4j database with vector + fulltext indexes

## Installation

```bash
.venv/bin/pip install neo4j-rust-ext "neo4j-graphrag>=1.13.0"

# Embedding provider (pick one):
.venv/bin/pip install openai          # OpenAI text-embedding-3-small / ada-002
.venv/bin/pip install cohere          # Cohere embed-english-v3.0
# Ollama: no extra install — uses HTTP API at localhost:11434
```

## Step K1 — Schema (model stage output)

The `model` stage should have produced `schema.cypher`. For KG/documents, it typically includes:

```cypher
CYPHER 25
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;

CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
  FOR (c:Chunk) ON (c.embedding)
  OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } };

CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
  FOR (e:Entity) ON EACH [e.name];
```

Apply this before running the pipeline (`load` step L0).

## Step K2 — Configure the pipeline

Generate `import/ingest_docs.py`:

```python
"""
import/ingest_docs.py — Build knowledge graph from documents using SimpleKGPipeline.
Usage: python3 import/ingest_docs.py [--docs-dir ./data/docs]
"""
import asyncio
import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# ── Embedding provider selection ──────────────────────────────────────────────
# Set EMBEDDING_PROVIDER in .env: openai | cohere | ollama
provider = os.environ.get("EMBEDDING_PROVIDER", "openai")
embedding_model = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")

if provider == "openai":
    from neo4j_graphrag.embeddings import OpenAIEmbeddings
    embedder = OpenAIEmbeddings(model=embedding_model)
    dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))

elif provider == "cohere":
    from neo4j_graphrag.embeddings import CohereEmbeddings
    embedder = CohereEmbeddings(model=embedding_model or "embed-english-v3.0")
    dimensions = 1024

elif provider == "ollama":
    from neo4j_graphrag.embeddings import OllamaEmbeddings
    embedder = OllamaEmbeddings(
        model=embedding_model or "nomic-embed-text",
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    dimensions = 768  # nomic-embed-text default

else:
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {provider}. Use openai, cohere, or ollama.")

# ── LLM selection ─────────────────────────────────────────────────────────────
llm_provider = os.environ.get("LLM_PROVIDER", "openai")
llm_model = os.environ.get("LLM_MODEL", "gpt-4o-mini")

if llm_provider == "openai":
    from neo4j_graphrag.llm import OpenAILLM
    llm = OpenAILLM(model_name=llm_model)
elif llm_provider == "anthropic":
    from neo4j_graphrag.llm import AnthropicLLM
    llm = AnthropicLLM(model_name=llm_model or "claude-haiku-4-5-20251001")
else:
    raise ValueError(f"Unknown LLM_PROVIDER: {llm_provider}. Use openai or anthropic.")

# ── Neo4j connection ──────────────────────────────────────────────────────────
driver = GraphDatabase.driver(
    os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
)

# ── Pipeline setup ────────────────────────────────────────────────────────────
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline

# Adapt entity types and relations to the domain from schema.json
ENTITIES = ["Person", "Organization", "Location", "Topic", "Product"]  # customize
RELATIONS = ["MENTIONS", "RELATED_TO", "WORKS_FOR", "LOCATED_IN"]      # customize
POTENTIAL_SCHEMA = [
    ("Person", "WORKS_FOR", "Organization"),
    ("Organization", "LOCATED_IN", "Location"),
    ("Person", "MENTIONS", "Topic"),
]

pipeline = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    embedder=embedder,
    entities=ENTITIES,
    relations=RELATIONS,
    potential_schema=POTENTIAL_SCHEMA,
    from_pdf=False,  # set True if processing PDF files
    neo4j_database=os.environ.get("NEO4J_DATABASE", "neo4j"),
)

# ── Document loading ──────────────────────────────────────────────────────────
def load_documents(docs_dir: str) -> list[str]:
    """Load .txt and .md files from directory."""
    texts = []
    for path in Path(docs_dir).glob("**/*.{txt,md}"):
        texts.append(path.read_text(encoding="utf-8"))
    return texts

async def ingest(docs_dir: str):
    docs = load_documents(docs_dir)
    print(f"Processing {len(docs)} documents...")
    for i, text in enumerate(docs, 1):
        print(f"  [{i}/{len(docs)}] {len(text)} chars")
        await pipeline.run_async(text=text)

    # Verify
    records, _, _ = driver.execute_query(
        "MATCH (n) RETURN labels(n)[0] AS l, count(n) AS c ORDER BY c DESC"
    )
    print("\nGraph summary:")
    for r in records:
        print(f"  {r['l']}: {r['c']}")
    driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", default="./data/docs")
    args = parser.parse_args()
    asyncio.run(ingest(args.docs_dir))
```

## Step K3 — .env additions needed

```bash
# Add to .env (already created by provision stage):
EMBEDDING_PROVIDER=openai          # openai | cohere | ollama
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
LLM_PROVIDER=openai                # openai | anthropic
LLM_MODEL=gpt-4o-mini
# OLLAMA_BASE_URL=http://localhost:11434  # only for ollama
```

## Step K4 — Run the pipeline

```bash
# Place documents in ./data/docs/
mkdir -p data/docs
# cp your .txt or .md files into data/docs/

python3 import/ingest_docs.py --docs-dir ./data/docs
```

## Step K5 — Post-ingestion: verify vector index

```bash
source .env
cypher-shell -a "$NEO4J_URI" -u "$NEO4J_USERNAME" -p "$NEO4J_PASSWORD" \
  "CYPHER 25 SHOW VECTOR INDEXES YIELD name, state, populationPercent RETURN name, state, populationPercent"
```

Wait for `state=ONLINE` and `populationPercent=100` before running vector queries.

## Step K6 — Test retrieval

```python
# Quick smoke test: does vector search return anything?
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.embeddings import OpenAIEmbeddings

embedder = OpenAIEmbeddings(model="text-embedding-3-small")
retriever = VectorRetriever(
    driver=driver,
    index_name="chunk_embeddings",
    embedder=embedder,
)
results = retriever.search(query_text="<your use-case question here>", top_k=3)
assert results.items, "No results — check vector index is ONLINE and documents were embedded"
for item in results.items:
    print(item.content[:200])
```

## Completion condition

- Documents ingested (each doc processed by pipeline)
- Vector index state = ONLINE
- `VectorRetriever.search()` returns ≥1 result on a test query
- `import/ingest_docs.py` saved in `import/` directory

## Common issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Vector index `POPULATING` | Index still building | Wait and re-check `populationPercent` |
| `EmbeddingError` | Missing API key | Set `OPENAI_API_KEY` / `COHERE_API_KEY` in `.env` |
| Empty chunks | Documents too short | Ensure each doc has ≥100 chars |
| Slow ingestion | Large docs + many entities | Use `gpt-4o-mini` for extraction; batch docs in parallel |
| Dimensions mismatch | Wrong `vector.dimensions` in index | Drop and recreate vector index matching your model's output |
