# neo4j-getting-started-skill

A Claude Code skill that guides a user or autonomous agent from **zero to a working Neo4j application** — in ≤15 minutes (autonomous) or ≤90 minutes (human-in-the-loop).

## What it does

The skill executes 8 ordered stages, each backed by a focused reference file:

```
0-prerequisites → 1-context → 2-provision → 3-model → 4-load
                → 5-explore → 6-query → 7-build
```

At the end the user has:
- A running Neo4j database (Aura Free, Aura Pro, or Docker)
- A schema with constraints and indexes
- Data loaded (demo, synthetic, CSV, or documents)
- A Cypher query library validated against the live DB
- A runnable application (Jupyter notebook, Streamlit app, FastAPI backend, GraphRAG pipeline, or MCP config)
- A browser URL to see the graph visually

## Repository layout

```
neo4j-getting-started-skill/   ← the skill (install this)
  SKILL.md                     ← orchestrator (8 stages, 7 success gates)
  AGENTS.md                    ← conventions for agents building/modifying this skill
  references/
    0-prerequisites.md … 7-build.md   ← one file per stage
    capabilities/
      execute-cypher.md        ← 3 execution methods (MCP, cypher-shell, HTTP)
      cypher-authoring.md      ← authoring rules + pitfalls table
      mcp-config.md            ← neo4j-mcp config for Claude Desktop / Claude Code
      kg-from-documents.md     ← GraphRAG ingestion pipeline
    domain-patterns.md         ← graph model templates by domain
neo4j-getting-started-skill-tests/
  personas/                  ← YAML personas (Alex, Sam, …)
  fixtures/                  ← Pre-populated work dirs for mid-flow testing
  harness/
    runner.py                ← integration test runner
    validator.py             ← 7-gate validation
  results/                   ← test run JSON output (git-ignored)

validate_cypher.py             ← syntax-validates all Cypher blocks in references/
test_load_scripts.py           ← validates Python load scripts against a live DB
aura.env                       ← Aura API credentials (git-ignored)
```

## Key design decisions

| Decision | Rationale |
|----------|-----------|
| SKILL.md is a thin orchestrator | Agent reads only the active stage reference; avoids >700-line system prompts |
| Stages have `progress.md` tracking | Enables resumability — if a run fails mid-flow, the next run picks up where it left off |
| Preferred load: DataFrame + `$rows` batches | Works on Aura (no file:// access); any data source via pandas |
| `CALL {} IN TRANSACTIONS` needs `session.run()` | `execute_query()` uses managed transactions which reject this clause |
| CYPHER 25 + QPP syntax throughout | Neo4j 2026.01+; `(()-[:R]->()){0,5}` replaces variable-length `[:R*0..5]` |
| Aura provisioning via direct REST (not CLI) | No extra binary needed; curl works everywhere |
| `graph_visible` is a hard success gate | Seeing nodes+edges rendered is the "it clicks" moment; never skip |
| v1 Python only | Focus on quality; JavaScript in phase 2 |

## Install the skill

```bash
make install-skill
# installs to ~/.claude/skills/neo4j-getting-started-skill/
```

Then trigger from any Claude Code session:
```
/neo4j-getting-started-skill
```

## Integration testing

Integration tests run Claude Code autonomously with a persona YAML and validate the produced files and database state against 7 success gates.

**Prerequisites:**

1. Copy `aura.env.example` → `aura.env` and add your credentials:
   ```
   CLIENT_ID=...
   CLIENT_SECRET=...
   PROJECT_ID=...          # recommended for multi-project accounts
   ORGANIZATION_ID=...     # recommended for multi-org accounts
   NEO4J_URI=...           # optional — pre-populates .env, skips provisioning
   NEO4J_PASSWORD=...
   ```
2. Install Python deps: `pip install python-dotenv pyyaml neo4j`

**Run tests:**

```bash
# Full end-to-end (provisions a real Aura instance)
make integration-alex
make integration-sam

# Start from stage 5-explore (stages 0-4 pre-populated from fixture)
make integration-alex-from-explore

# Validate all Cypher blocks in references/ (requires localhost:7687, db=jtbd)
make test-cypher

# Validate Python load scripts
make test-load

# Check skill file structure (no Claude, no DB)
make test-quick
```

**How the runner works:**
- Creates a fresh `tempdir` for each run — no source directory pollution
- Copies `aura.env` into the work dir; if it contains `NEO4J_URI`+`NEO4J_PASSWORD`, writes `.env` automatically (skips provisioning stage)
- Installs the skill to `~/.claude/skills/`, runs Claude via `--append-system-prompt`, uninstalls on exit
- Streams Claude's output live; prints `[tool]` lines for each tool call
- After the run, validates all 7 success gates against the work dir and live DB

**Fixture-based testing** (`neo4j-getting-started-skill-tests/fixtures/alex_after_load/`):
Pre-populates stages 0-4 so the test only exercises stages 5-7.
Used by `make integration-alex-from-explore`. The `__NEO4J_URI__` placeholder in `progress.md` is substituted at runtime from `aura.env`.

## Success gates

| Gate | Stage | Condition |
|------|-------|-----------|
| `db_running` | provision | `driver.verify_connectivity()` succeeds |
| `model_valid` | model | ≥2 node labels, ≥1 rel type, ≥1 constraint in DB |
| `data_present` | load | `MATCH (n) RETURN count(n)` ≥ 50 |
| `queries_work` | query | ≥5 queries; ≥2 traversals; ≥3 return ≥1 result |
| `graph_visible` | explore | Browser URL or notebook viz delivered |
| `app_generated` | build | Artifact exists, passes syntax, returns non-empty results |
| `integration_ready` | build | MCP config present (if requested) |

## Assumptions

- Claude Code is available as `claude` on PATH
- Python ≥3.10
- `neo4j-mcp` binary is downloaded during the `prerequisites` stage (or pre-installed)
- Aura Free has a 1-3 min provisioning wait; this does not count against the 15-min budget
- GDS (Graph Data Science) is not available on Aura Free — the skill guards all GDS queries
- `CALL {} IN TRANSACTIONS` requires `session.run()`, not `execute_query()` — validated in test harness
