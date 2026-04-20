# neo4j-getting-started-skill

A Claude Code skill for the complete Neo4j getting-started journey.

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

Or with context upfront:
```
/neo4j-getting-started-skill I want to build a friend recommendation system using Python. I'm a beginner.
```

## What happens

The skill runs 8 stages in order:

| Stage | What it does |
|-------|-------------|
| `0-prerequisites` | Downloads `neo4j-mcp` binary, sets up `.gitignore` |
| `1-context` | Collects domain, use-case, experience, DB target, data source, app type |
| `2-provision` | Provisions Aura Free/Pro or connects to Docker/existing DB; writes `.env` |
| `3-model` | Designs or discovers a graph schema; writes `schema.json` + `schema.cypher` |
| `4-load` | Applies constraints; loads demo/synthetic/CSV/document data |
| `5-explore` | Generates Neo4j Browser URL for visual exploration |
| `6-query` | Generates and validates a Cypher query library (`queries.cypher`) |
| `7-build` | Generates a runnable app (notebook, Streamlit, FastAPI, GraphRAG, or MCP config) |

## Resumability

The skill writes `progress.md` after each stage. If a session is interrupted, the next invocation reads `progress.md`, finds the first `status: pending` stage, and resumes from there without re-asking questions.

## Files produced

```
.env                    ← DB connection credentials
schema.json             ← graph model definition
schema.cypher           ← DDL (constraints + indexes)
import/                 ← data loading scripts
reset.cypher            ← wipe data, keep schema
queries.cypher          ← validated Cypher query library
notebook.ipynb          ← (if APP_TYPE=notebook)
app.py                  ← (if APP_TYPE=streamlit)
main.py                 ← (if APP_TYPE=fastapi)
graphrag_app.py         ← (if APP_TYPE=graphrag)
.claude/settings.json   ← (if APP_TYPE=mcp or integration=mcp)
requirements.txt
progress.md             ← stage-by-stage progress log
```

## Modes

**HITL** (human-in-the-loop): pauses after `model` and `load` for review.

**Autonomous** (no user response within ~60s): uses defaults (Aura Free → synthetic data → Python notebook), auto-approves all stages, targets ≤15 min from DB running.

## Configuration

The skill reads credentials from two separate files:

- **`aura.env`** — Aura API credentials for provisioning (never overwritten)
- **`.env`** — DB connection details written by the provision stage

See `references/2-provision.md` for the Aura API credential setup.
