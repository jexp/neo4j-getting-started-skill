# neo4j-getting-started-skill

A Claude Code skill for the complete Neo4j getting-started journey — from zero to a
running graph application in one session.

## Prerequisites

- **Claude Code** (CLI or IDE extension)
- **Python ≥ 3.10** (`python3 --version`)
- **Docker** — only required if `db_target=local-docker`
- **Aura API credentials** in `aura.env` — only required if `db_target=aura-free` or `aura-pro`

## Installation

```bash
# From the repo root
make install-skill
```

Or manually:
```bash
cp -R . ~/.claude/skills/neo4j-getting-started-skill/
```

## Usage

Start any Claude Code session in an empty directory and trigger the skill:

```
/neo4j-getting-started-skill
```

Any context you include is extracted from natural language — no special syntax needed.
Stage 1 asks for anything that's still missing, so all context is optional upfront:

```
/neo4j-getting-started-skill I want to build a friend recommendation system. I'm a beginner.
```

```
/neo4j-getting-started-skill Healthcare patient journey analysis, intermediate Python dev,
running on local Docker, generate synthetic data, Jupyter notebook please.
```

```
/neo4j-getting-started-skill fraud detection for a fintech startup
```

**Autonomous mode** kicks in when all 6 variables (domain, use-case, experience, db target,
data source, app type) can be inferred from your message — the skill then runs all 8 stages
without stopping. If any are missing, stage 1 asks for them conversationally before proceeding.

## What happens

The skill runs 8 stages in order:

| Stage | What it does |
|-------|-------------|
| `0-prerequisites` | Downloads `neo4j-mcp` binary, creates `.venv`, sets up `.gitignore` |
| `1-context` | Collects domain, use-case, experience, DB target, data source, app type |
| `2-provision` | Provisions or connects to a Neo4j database; writes `.env` |
| `3-model` | Designs a graph schema; writes `schema.json` + `schema.cypher` |
| `4-load` | Applies constraints; loads demo/synthetic/CSV/document data |
| `5-explore` | Opens Neo4j Browser for visual exploration; runs `neo4j-viz` preview |
| `6-query` | Generates and validates a Cypher query library (`queries/queries.cypher`) |
| `7-build` | Generates a runnable app; installs dependencies into `.venv` |

## Database targets (`db_target`)

| Value | What happens |
|-------|-------------|
| `aura-free` | Creates a new Aura Free instance via REST API (requires `aura.env`) |
| `aura-pro` | Creates an Aura Professional instance (requires `aura.env`) |
| `local-docker` | Runs `neo4j:enterprise` in Docker on `localhost:7687` — Docker must be installed |
| `local-desktop` | Connects to a running Neo4j Desktop instance on `localhost:7687` |
| `existing-cloud` | Connects to any existing Neo4j instance — you provide URI + password |

For `local-docker`, the skill pulls `neo4j:enterprise`, mounts a `./neo4j-data/` volume for
persistence, and waits up to 90 s for Bolt to be ready. No extra setup needed beyond Docker.

## Data sources (`data_source`)

| Value | What happens |
|-------|-------------|
| `synthetic` | Generates realistic fake data in Python (`data/generate.py` + `data/import.py`) |
| `demo` | Loads a Neo4j public demo dataset (Movies, Northwind, etc.) |
| `csv` | Imports your own CSV files from `data/` |
| `documents` | Builds a knowledge graph from documents using `neo4j-graphrag` (GraphRAG path) |

## App types (`app_type`)

| Value | Output | Run command |
|-------|--------|-------------|
| `notebook` | `notebook.ipynb` with schema, viz, and use-case cells | `.venv/bin/jupyter notebook notebook.ipynb` |
| `streamlit` | `app.py` dashboard with sidebar controls + graph viz | `.venv/bin/streamlit run app.py` |
| `fastapi` | `main.py` REST API with `/health` + use-case endpoints | `.venv/bin/uvicorn main:app --reload` |
| `graphrag` | `graphrag_app.py` hybrid vector+graph retrieval pipeline | `.venv/bin/python3 graphrag_app.py` |
| `mcp` | `.claude/settings.json` MCP server config for Claude Code | restart Claude Code |
| `explore-only` | `queries/queries.cypher` + `README.md` only — no app | — |

## Modes

**HITL** (human-in-the-loop, default): pauses at key checkpoints — after schema design and
after data load — for user review before proceeding.

**Autonomous**: when all 6 context variables (`domain`, `use_case`, `experience`, `db_target`,
`data_source`, `app_type`) are present in the initial prompt, the skill skips all HITL pauses
and runs end-to-end without interruption. Target completion: ≤15 min (local Docker) or
≤25 min (Aura provisioning included).

## Resumability

The skill writes `progress.md` after each stage. If a session is interrupted, invoke the
skill again in the same directory — it reads `progress.md`, finds the first `status: pending`
stage, and resumes from there without re-asking questions.

## Files produced

```
.env                    ← DB connection credentials (gitignored)
progress.md             ← stage-by-stage progress log
requirements.txt        ← Python dependencies
README.md               ← generated project README
.venv/                  ← Python virtual environment (gitignored)

schema/
  schema.json           ← graph model definition
  schema.cypher         ← DDL: constraints + indexes
  reset.cypher          ← wipe data, keep schema

data/
  generate.py           ← synthetic data generator  (data_source=synthetic)
  import.py             ← CSV/file importer          (data_source=csv)
  *.csv                 ← data files

queries/
  queries.cypher        ← validated Cypher query library (≥5 queries, ≥3 traversal)

notebook.ipynb          ← (app_type=notebook)
app.py                  ← (app_type=streamlit)
main.py                 ← (app_type=fastapi)
graphrag_app.py         ← (app_type=graphrag)
.claude/settings.json   ← (app_type=mcp or integration=mcp)
```

**Input credential files** (not generated by the skill — you provide these):
```
aura.env                ← Aura API credentials (gitignored); see references/2-provision.md
```

## MCP integration

When `app_type=mcp` or `integration=mcp`, the skill writes a `neo4j` MCP server config
pointing at the local `neo4j-mcp` binary. After restarting Claude Code you can ask questions
about your graph in natural language: "What node labels exist?", "Show me the top 10 patients
by encounter count", etc.

Available MCP tools: `get-schema`, `read-cypher`, `write-cypher`, `list-gds-procedures`.

## Running tests

```bash
# Single persona
make integration-elena       # local Docker — healthcare notebook
make integration-alex        # Aura — social network notebook
make integration-priya       # Aura — fraud detection FastAPI

# All personas (sequential)
python3 tests/harness/runner.py --all-personas

# Keep Docker container after run (for manual inspection)
make integration-elena       # container kept running by default
# Stop it later:
docker stop neo4j-elena-test && docker rm neo4j-elena-test
```

Test results land in `tests/results/`. Each run produces a JSON gate report and a DB snapshot.

## Configuration

| File | Purpose |
|------|---------|
| `aura.env` | Aura API `CLIENT_ID` + `CLIENT_SECRET` for provisioning new instances |
| `.env` | DB connection URI, username, password, database — written by the provision stage |

See `references/2-provision.md` for Aura credential setup.
