---
name: neo4j-getting-started-skill
description: >
  Orchestrates the full journey from zero to a running Neo4j application.
  Executes 8 named stages in order: prerequisites → context → provision →
  model → load → explore → query → build. Each stage has its own reference
  file in references/ that the agent reads and follows when entering that stage.
  Supports both HITL and fully autonomous operation.
  Time budget: ≤15 min after DB is running (autonomous), ≤90 min total (HITL).
version: 0.3.0
allowed-tools: Bash, WebFetch, Read, Write, Edit,
  mcp__neo4j__read-cypher, mcp__neo4j__write-cypher, mcp__neo4j__get-schema,
  mcp__neo4j__list-gds-procedures,
  mcp__neo4j_data_modeling__validate_data_model,
  mcp__neo4j_data_modeling__visualize_data_model
compatibility: claude-code, cursor, windsurf, any-agent-with-bash
---

# Neo4j Getting-Started Skill

Guide a **user or agent** from zero to a working Neo4j application by executing the 8 stages below in order.

**At the start of each stage**: read the corresponding `${CLAUDE_SKILL_DIR}/references/<stage-name>.md` file and follow its instructions. Only load the stage you are currently executing — not all at once.

**"User" means both a human developer and an autonomous coding agent.**

---

## Project Structure

**All generated code, data, scripts, queries, and notebooks must be written to the working directory** so the user can inspect, reuse, and re-run them after the session ends. Never generate output only as text in the conversation — always write it to a file.

Organize files into this layout. Create subdirectories before writing files.

```
.env                    ← DB credentials (gitignored, loaded by python-dotenv)
aura.env                ← Aura API credentials (gitignored, never overwrite)
progress.md             ← stage-by-stage progress (this skill writes it)
requirements.txt        ← Python dependencies

schema/
  schema.json           ← graph model definition
  schema.cypher         ← DDL: constraints + indexes
  reset.cypher          ← wipe all data (keep schema)

data/
  generate.py           ← synthetic data generator  (DATA_SOURCE=synthetic)
  import.py             ← CSV/file importer          (DATA_SOURCE=csv or relational)
  *.csv                 ← any provided or generated data files

queries/
  queries.cypher        ← validated Cypher query library

scripts/
  provision_aura.py     ← Aura provisioning script (generated during provision stage)

notebook.ipynb          ← app artifact (root — standard jupyter convention)
app.py                  ← app artifact (root — streamlit run app.py)
main.py                 ← app artifact (root — uvicorn main:app)
graphrag_app.py         ← app artifact (root)
```

Root-level files (`.env`, `requirements.txt`, app code) stay at root because tooling expects them there. Everything else goes in the appropriate subfolder.

---

## Progress Tracking

The skill maintains `progress.md` in the working directory to support resumability.

**On startup:**
1. Check if `progress.md` exists.
2. If it exists, find the first pending stage:
   ```bash
   grep -B1 "^status: pending" progress.md | grep "^###" | head -1
   ```
3. Resume from that stage. Read its context block (the key=value lines beneath the header) to restore `DOMAIN`, `USE_CASE`, `NEO4J_URI`, etc. — do not re-ask the user for information already recorded.
4. For each completed stage, read every file listed in its `files=` line before proceeding. These files are the ground truth — do not reconstruct their content from memory.
   - `schema/schema.json` → re-read before model, load, query, or build stages
   - `queries/queries.cypher` → re-read before build stage
   - `data/generate.py` → re-read before import or reset
5. If `progress.md` does not exist, start from `0-prerequisites`.

**On stage completion** — update (or create) `progress.md`:
- If the stage's `###` section already exists, update `status: pending` → `status: done` and append any new key=value lines.
- If the section doesn't exist, append it following the format below.

**Format:**
```markdown
# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done

### 1-context
status: done
DOMAIN=social
USE_CASE=friend recommendations
EXPERIENCE=beginner
DB_TARGET=aura-free
DATA_SOURCE=synthetic
APP_TYPE=notebook
EXEC_METHOD=query-api

### 2-provision
status: done
NEO4J_URI=neo4j+s://abc123.databases.neo4j.io

### 3-model
status: done
labels=Person,Post
relationships=FOLLOWS,POSTED
constraints=2

### 4-load
status: done
nodes=200 Person, 50 Post
relationships=1400 FOLLOWS, 300 POSTED

### 5-explore
status: pending

### 6-query
status: pending

### 7-build
status: pending
```

---

## Execution Protocol

For each stage:
1. Announce the stage: `"## Stage: <name> — <purpose>"`
2. Read `${CLAUDE_SKILL_DIR}/references/<name>.md`
3. Execute the instructions in that file
4. Verify the stage's completion condition
5. Update `progress.md` with `status: done` and stage-specific context
6. Proceed to the next stage (HITL: pause for approval first)

If a stage fails, recover using the error guidance in the stage reference file. Do not skip stages unless the skip condition below explicitly permits it.

---

## Stages

Stages run in the numbered order shown. Each depends on the one before it completing successfully (except where a skip condition applies). Read the linked reference file when entering each stage.

```
0-prerequisites → 1-context → 2-provision → 3-model → 4-load → 5-explore → 6-query → 7-build
```

Shared capabilities used across multiple stages:
- Cypher execution: `${CLAUDE_SKILL_DIR}/references/capabilities/execute-cypher.md` (3 options; `EXEC_METHOD` chosen in `context`)
- Cypher authoring rules: `${CLAUDE_SKILL_DIR}/references/capabilities/cypher-authoring.md` (or defer to `neo4j-cypher-authoring-skill`)
- MCP configuration: `${CLAUDE_SKILL_DIR}/references/capabilities/mcp-config.md` (used in `prerequisites` and `build`)
- Query validation: `${CLAUDE_SKILL_DIR}/scripts/validate_queries.py` — batch-validate all queries in one call (used in `query`)

---

### 0 — `prerequisites`
**Purpose**: Verify and install required CLI tools before doing anything else.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/0-prerequisites.md`  
**Completes when**: `neo4j-mcp` binary is reachable; `.gitignore` has `.env` entry.  
**Never skip.**

---

### 1 — `context`
**Purpose**: Collect domain, use-case, experience, infrastructure target, data source, and output type. Detect `EXEC_METHOD` for Cypher execution.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/1-context.md`  
**Completes when**: `DOMAIN`, `USE_CASE`, `EXPERIENCE`, `DB_TARGET`, `DATA_SOURCE`, `APP_TYPE`, `EXEC_METHOD` are known.  
**Skip condition**: all variables already provided in conversation context.

---

### 2 — `provision`
**Purpose**: Provision a running Neo4j database and save credentials to `.env`.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/2-provision.md`  
**Completes when**: `.env` exists with `NEO4J_URI/USERNAME/PASSWORD/DATABASE`; connectivity verified.  
**Skip condition**: `DB_TARGET=existing` → write `.env` from user credentials, proceed to `3-model`.

---

### 3 — `model`
**Purpose**: Design or discover a graph data model suited to the use-case.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/3-model.md`  
**Completes when**: `schema.json` and `schema.cypher` written.  
**Skip condition**: `DATA_SOURCE=demo` → use demo schema, proceed to `4-load`.  
**HITL checkpoint**: show model draft to user, wait for approval before continuing.

---

### 4 — `load`
**Purpose**: Apply schema constraints, then import data (demo, synthetic, CSV, or documents).  
**Reference**: `${CLAUDE_SKILL_DIR}/references/4-load.md`  
**Depends on**: `3-model` (constraints must exist before import).  
**Completes when**: node count ≥ 50; `import/` scripts written; `reset.cypher` written.

---

### 5 — `explore`
**Purpose**: Deliver a visual entry point to the graph — the "it clicks" moment.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/5-explore.md`  
**Completes when**: browser URL printed to user, or notebook visualization cell added.  
**Hard gate — never skip.**

---

### 6 — `query`
**Purpose**: Generate and validate a Cypher query library for the use-case.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/6-query.md`  
**Completes when**: `queries.cypher` has ≥5 queries; ≥2 traversals; ≥3 return results.

---

### 7 — `build`
**Purpose**: Generate a runnable application, dashboard, notebook, or agent integration.  
**Reference**: `${CLAUDE_SKILL_DIR}/references/7-build.md`  
**Completes when**: artifact exists, passes syntax check, returns non-empty use-case results.

---

## Success Gates (all 7 required)

| Gate | Stage | Condition |
|------|-------|-----------|
| `db_running` | provision | `driver.verify_connectivity()` succeeds |
| `model_valid` | model | ≥2 node labels, ≥1 rel type, ≥1 constraint in DB |
| `data_present` | load | `MATCH (n) RETURN count(n)` ≥ 50 |
| `queries_work` | query | ≥5 queries; ≥2 traversals; ≥3 return ≥1 result |
| `graph_visible` | explore | Browser URL or notebook viz delivered to user |
| `app_generated` | build | Artifact exists, passes syntax, returns non-empty results |
| `integration_ready` | build | MCP config or agent framework code present (if requested) |

---

## Fast Paths

| Situation | Action |
|-----------|--------|
| `DB_TARGET=existing` | Skip `provision`; write `.env` from user creds; go to `model` |
| `DATA_SOURCE=demo` | Skip custom modeling; use demo schema; jump to `load` |
| `DB_TARGET=existing` + data present | Skip `provision`, `model`, `load`; introspect schema; go to `explore` |

---

## HITL vs Autonomous Mode

**HITL** (user responds within ~60s): pause after `model` and `load` for review; pause after `explore` for visual confirmation.

**Autonomous** (no response, CI-like, `--auto-approve`): use defaults (Aura Free → synthetic data → Python notebook); auto-approve all stages; print browser URL to stdout; target ≤15 min from DB running.

Detect mode: no user response within ~60s → switch to autonomous defaults.

---

## Final Summary (deliver after all gates pass)

**Step 1 — write `README.md`** to the working directory using the template below.
Fill in every `<placeholder>` from `progress.md` and the actual generated files.
This is a required output — do not skip it.

```markdown
# <DOMAIN> Graph — <USE_CASE>

A synthetic <DOMAIN> graph built with Neo4j, covering <USE_CASE>.
Generated by the neo4j-getting-started-skill on <date>.

## What's in the graph

| Label | Count | Description |
|-------|-------|-------------|
| <Label> | <N> | <one line> |

**Relationships:** <TYPE1>, <TYPE2>, ...  
**Constraints:** <N> uniqueness constraints applied

## Explore visually

Open in Neo4j Browser:
<browser_url>

Starter query:
```cypher
MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 50
```

## Files

| File | Purpose | Re-run |
|------|---------|--------|
| `schema/schema.json` | Graph model | — |
| `schema/schema.cypher` | Constraints + indexes | `cypher-shell ... --file schema/schema.cypher` |
| `schema/reset.cypher` | Wipe data, keep schema | `cypher-shell ... --file schema/reset.cypher` |
| `data/generate.py` | Regenerate synthetic data | `python3 data/generate.py` |
| `data/import.py` | Re-import CSVs into Neo4j | `python3 data/import.py` |
| `queries/queries.cypher` | Query library | Paste into Neo4j Browser |
| `<artifact>` | <app type> | `<run command>` |
| `requirements.txt` | Python dependencies | `pip install -r requirements.txt` |

## Run the app

```bash
pip install -r requirements.txt
<run command>
```

## Reset and reload

```bash
cypher-shell ... --file schema/reset.cypher   # wipe data
python3 data/generate.py                       # regenerate CSVs
python3 data/import.py                         # reload
```

## Next steps

- Explore [GraphAcademy](https://graphacademy.neo4j.com) to deepen your Neo4j knowledge
- Edit `data/*.csv` to change the dataset, then re-run `data/import.py`
- Extend the model: add new node labels or relationship types in `schema/schema.json`
```

**Step 2 — print this to the conversation:**

```
✓ Neo4j Getting-Started — Complete

Database:  <NEO4J_URI>
Browser:   https://browser.neo4j.io/?connectURL=<encoded>

── What was generated (keep these files) ───────────────────────
schema/schema.json       Graph model definition
schema/schema.cypher     Re-apply constraints/indexes:  cypher-shell ... --file schema/schema.cypher
schema/reset.cypher      Wipe data, keep schema:        cypher-shell ... --file schema/reset.cypher
data/generate.py         Regenerate synthetic data:     python3 data/generate.py
data/*.csv               Source data files — edit to change the dataset
data/import.py           Re-import from CSVs:           python3 data/import.py
queries/queries.cypher   Query library — paste into Neo4j Browser or run with cypher-shell
<app-file>               <run-command>
requirements.txt         Install deps:                  pip install -r requirements.txt

── Gates ───────────────────────────────────────────────────────
db_running ✓  model_valid ✓  data_present ✓  queries_work ✓
graph_visible ✓  app_generated ✓  integration_ready ✓/–

── Next steps ──────────────────────────────────────────────────
- Explore:   open the Browser URL → run MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 50
- Iterate:   edit data/*.csv → python3 data/import.py (reset first with schema/reset.cypher)
- Learn:     https://graphacademy.neo4j.com
```

Omit lines that don't apply (e.g. omit `data/import.py` when `DATA_SOURCE=synthetic`,
omit `data/generate.py` when `DATA_SOURCE=csv`).
