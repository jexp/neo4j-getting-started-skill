# AGENTS.md — Agentic Engineering Guide

This file captures what we have learned building and testing this skill. It doubles as a
reference for writing good agentic skills in general.

---

## What a Skill Is

A skill is a reusable instruction set — a markdown file with YAML frontmatter — that
an AI coding agent executes to accomplish a multi-step task. It is not a chatbot prompt.
It is closer to a runbook: a precise sequence of stages with explicit completion conditions,
error recovery, and verifiable outputs.

The key insight: **a skill captures information that pushes the agent beyond its defaults.**
Everything Claude already knows well (Python syntax, REST APIs, standard library usage)
does not need to be in the skill. What does belong: domain-specific gotchas, non-obvious
tool invocation patterns, workflow constraints, and the exact shape of expected outputs.

---

## Skill File Structure

```
my-skill/
├── SKILL.md                  ← entry point: frontmatter + stage orchestration
├── AGENTS.md                 ← this file: contributor guide + learnings
├── references/
│   ├── 0-prerequisites.md    ← one file per stage; loaded on demand
│   ├── 1-context.md
│   ├── ...
│   └── capabilities/         ← cross-cutting concerns (auth, cypher, etc.)
└── tests/
    ├── personas/             ← YAML test cases (one per user archetype)
    ├── harness/              ← runner.py + validator.py
    └── results/              ← JSON reports per run
```

### SKILL.md frontmatter

```yaml
---
name: my-skill
description: >
  One-paragraph summary of what the skill does and when to invoke it.
  Written in third person. Front-load use-cases and keywords.
  Discovery depends on this field — treat it like a tool description.
version: 0.1.0
allowed-tools: Bash, Read, Write, Edit   # pre-approve what the skill needs
compatibility: claude-code, cursor, windsurf
---
```

The `description` field is your **discovery prompt**. If the skill isn't triggering when
expected, the description is wrong — not the skill body. Write it like a tool docstring:
what it does, when to use it, what it produces.

---

## Stage Design Principles

### One reference file per stage, loaded on demand

Split the skill body into numbered stage reference files. The agent reads only the file
for the current stage — not all at once. This:
- Keeps the active context window small
- Prevents earlier stage instructions from contaminating later stages
- Makes the skill maintainable: each file has a clear scope

```
# In SKILL.md:
At the start of each stage: read ${CLAUDE_SKILL_DIR}/references/<stage>.md
Only load the stage you are currently executing — not all at once.
```

### Each stage reference file must contain

1. **Purpose** — one sentence: what this stage does and why
2. **Steps** — numbered, concrete, with exact commands
3. **Completion condition** — explicit, verifiable (not "when you feel done")
4. **Error recovery** — what to do when it fails (not just the success path)
5. **On Completion** — exact format for writing to `progress.md`

### Completion conditions must be machine-checkable

Weak: "when the data looks right"
Strong: `MATCH (n) RETURN count(n) >= 50`

Weak: "when the app is built"
Strong: "file exists + `py_compile` passes + returns non-empty results on the use-case query"

The completion condition is also your success gate definition. Write them together.

### Resumability via progress.md

Every stage writes a structured key=value block to `progress.md`. On startup, the skill
reads this file to restore state — no re-asking the user for things already recorded.

```markdown
### 3-model
status: done
labels=Person,Post
relationships=FOLLOWS,POSTED
constraints=2
files=schema/schema.json,schema/schema.cypher
```

This pattern enables autonomous retries, partial failure recovery, and interrupted-session
resume. The `files=` line is critical: on resume, the agent re-reads every listed file
before proceeding. Memory is unreliable across turns; files are not.

---

## HITL vs Autonomous Mode

**HITL is the default.** Never auto-mode on a bare invocation.

The failure mode: the agent fills in defaults for every missing variable, counts them as
"explicitly provided", and launches into a 15-minute autonomous run — provisioning cloud
resources, writing files, starting Docker — before the user has typed a single word.

### The correct detection rule

```
AUTONOMOUS only if ALL required variables are EXPLICITLY stated in the initial prompt.
Defaults do not count. Inferred values do not count.

HITL in all other cases, including:
- Bare skill invocation with no parameters
- "help me", "get started", "guide me" — intent, not parameters
- Any variable that can only be filled in by applying a default
```

### HITL mode must ask before doing anything

The first HITL response is questions only — no file writes, no shell commands, no
provisioning. Ask all missing questions in one combined message, not one at a time.

### Autonomous mode never pauses

Once in autonomous mode, every HITL checkpoint is skipped. No "does this look right?",
no approval requests, no pauses. The only output is progress updates and the final summary.

---

## Success Gates

Define 5–7 binary gates per skill. Each gate:
- Has a unique string ID (`db_running`, `data_present`, etc.)
- Maps to a single, deterministic check
- Has a clear pass condition stated in the persona YAML
- Is checked by the validator after the skill completes — not during

### Gate design principles

**Gates check outcomes, not implementation.** Don't check "did the agent run
`data/import.py`" — check "are there ≥50 nodes in the DB". This lets the skill choose
its own path while still being accountable.

**Hard gates vs soft gates.** Some gates must pass for the run to count (hard). Others
are informational (logged, not blocking). The `graph_visible` gate — must deliver a
browser URL — is a hard gate. It is the "it clicks" moment for new users and must never
be skipped, even when the agent is rushing through stages 5–7.

**Avoid threshold ambiguity.** `count(n) >= 50` is unambiguous. "The app works" is not.
If a gate can't be written as a deterministic check, it belongs in a human review step.

### This skill's gates

| Gate | Check | Rationale |
|------|-------|-----------|
| `db_running` | `driver.verify_connectivity()` | Nothing works without this |
| `model_valid` | ≥3 constrained node labels in `SHOW CONSTRAINTS` | Schema was actually applied |
| `data_present` | `count(n)` ≥ persona threshold | Data loading ran to completion |
| `queries_work` | ≥N of M queries return ≥1 row | Queries match the loaded schema |
| `graph_visible` | `browser_url=` in `5-explore` section of `progress.md` | The "it clicks" moment — hard gate |
| `app_generated` | File exists + `py_compile` passes | Runnable artifact delivered |
| `time_budget` | elapsed ≤ persona timeout | Autonomous run is practical to use |

---

## Persona-Based Testing

A persona is a YAML test case representing one user archetype. It drives a full
autonomous run and is validated against the success gates.

### Persona YAML structure

```yaml
persona:
  id: alex_beginner
  name: Alex
  description: "First time with graph DBs. Personal social network project."
  experience: beginner
  background: "Knows basic Python, no graph DB experience"

inputs:
  domain: social
  use_case: "friend recommendations and community discovery"
  db_target: aura-free
  data_source: synthetic
  app_type: notebook

expected_outputs:
  files: [.env, schema/schema.json, ...]
  db_state:
    min_node_labels: 3
    min_rel_types: 2
    min_nodes: 50
  queries:
    min_count: 5
    min_returning_results: 3

success_gates:
  - id: db_running
    check: "driver.verify_connectivity() does not throw"
  # ...

test_config:
  mode: autonomous
  timeout_seconds: 900
  fixture_dir: "fixtures/alex_data"     # optional: pre-seed files into work_dir
  env_passthrough: [OPENAI_API_KEY]     # keys to copy from aura.env → .env
```

### Persona coverage strategy

Cover at least:
- One beginner (demo data, managed cloud, notebook)
- One intermediate (CSV data, real queries, web app)
- One advanced (documents/LLM extraction, embeddings, GraphRAG)
- One with pre-existing data (skip provision + model; test explore/query/build only)

Each persona exercises a distinct code path. If two personas hit the same stages with
the same data source, merge them or differentiate further.

### What makes a good persona

- **Realistic background**: "5 years Python, no graph experience" shapes how the skill explains things
- **Concrete use-case**: "fraud ring detection" not "financial analysis"
- **Tight time budget**: generous timeouts hide slow paths; tight budgets force efficiency
- **Meaningful thresholds**: `min_nodes: 10` catches nothing; `min_nodes: 50` with `min_returning_results: 3` does

---

## What Belongs in a Skill (and What Doesn't)

| Belongs | Does not belong |
|---------|----------------|
| Domain-specific tool invocation patterns | Standard Python/Bash usage |
| Non-obvious API quirks (e.g. cloud polling) | What REST APIs are |
| Exact output file formats for resumability | Generic file I/O |
| Workflow ordering constraints | Basics the LLM already knows |
| Concrete error recovery steps | "Debug if it fails" advice |
| Hard completion conditions with thresholds | Open-ended quality judgments |
| Gotchas discovered during testing | Things discoverable from docs |

The **Gotchas section is the highest-value content** in a skill. It captures real errors
found during testing and prevents them from repeating. Treat it as a living document —
update it every time a test run surfaces a new failure class.

---

## Anti-Patterns

**Over-prompting.** A 2000-line SKILL.md explaining things Claude already knows. Every
line consumes context on every invocation. Test: "would a senior engineer know this
without being told?" If yes, remove it.

**One giant file.** Loading all stage instructions at once pollutes the context window
for every subsequent turn. Use progressive disclosure: one file per stage, loaded only
when that stage starts.

**Vague completion conditions.** "When the data looks right" is not a completion
condition. Define exact, machine-checkable criteria for every stage.

**No error recovery.** Documenting only the happy path. Every stage needs a short
"Error recovery" section covering the most common failure.

**Inferred autonomous mode.** Filling in defaults to satisfy the "all variables present"
threshold. A user who typed the skill name with no parameters is in HITL mode.

**Schema-first neglect.** Writing Cypher queries without first inspecting the actual
labels and relationships in the DB. Queries break when the LLM assumes labels that
differ from what was loaded — especially with LLM-based extraction pipelines where
entity labels are non-deterministic.

**Shipping helper scripts in the skill repo.** A `scripts/` directory in a skill repo
triggers Snyk/Socket security scanners (post-install hook pattern). Inline helper scripts
as code blocks in the reference markdown instead — the agent writes them to the work
directory at runtime.

**Committing .env.** Write `.gitignore` with `.env` entry before writing any credentials
file. This must happen in the prerequisites stage, not as an afterthought.

---

## Gotchas from This Skill

These are the kinds of things worth documenting — non-obvious, learnt from failure:

**SimpleKGPipeline does not create the vector index.**
Embeddings are stored on `:Chunk(embedding)` but no index is created. Call
`create_vector_index()` from `neo4j_graphrag.indexes` explicitly after ingestion.

**All extracted entities are stored under `:__KGBuilder__`.**
Domain labels in `schema={}` guide LLM extraction but do not become Neo4j labels.
Queries and `retrieval_query` patterns must use `:__KGBuilder__` + `[:FROM_CHUNK]`.

**Document ingestion must run synchronously.**
LLM-based extraction takes minutes. Launching with `&` means zero nodes in the DB
when subsequent stages run. Wait for the explicit completion message.

**HITL detection is broken by defaults.**
If the skill defines defaults for all variables, the agent can satisfy "all variables
present" from those defaults alone — triggering autonomous mode on a bare invocation.

**schema.cypher OPTIONS blocks are fragile.**
The `split(";")` parser used in `apply_schema()` fails on `CREATE VECTOR INDEX` with
backtick-quoted property names inside the OPTIONS block. Create vector indexes
programmatically instead.

**The `graph_visible` gate gets skipped under context pressure.**
After a long load stage, the agent abbreviates stages 5–7 without writing to
`progress.md`. Make the `browser_url` write an explicit hard requirement with timing:
"write this immediately after generating the URL, before moving to the next stage".

---

## This Skill's Commands

```bash
# Run a single persona test
cd neo4j-getting-started-skill-tests
make integration-alex
make integration-marcus

# Run with verbose output
uv run python harness/runner.py --persona personas/alex_beginner.yml --verbose

# Keep the provisioned DB after the run (for inspection)
uv run python harness/runner.py --persona personas/alex_beginner.yml --keep-db
```

---

## File Locations

```
neo4j-getting-started-skill/          ← the skill
├── SKILL.md
├── AGENTS.md
├── references/
│   ├── 0-prerequisites.md
│   ├── 1-context.md
│   ├── 2-provision.md
│   ├── 3-model.md
│   ├── 4-load.md
│   ├── 5-explore.md
│   ├── 6-query.md
│   ├── 7-build.md
│   ├── domain-patterns.md
│   └── capabilities/
│       ├── cypher-authoring.md
│       ├── execute-cypher.md
│       ├── kg-from-documents.md
│       └── mcp-config.md

neo4j-getting-started-skill-tests/    ← test harness (separate from skill)
├── Makefile
├── harness/
│   ├── runner.py
│   └── validator.py
├── personas/
│   ├── alex_beginner.yml
│   ├── priya_analyst.yml
│   ├── sam_developer.yml
│   ├── elena_healthcare.yml
│   └── marcus_legal.yml
├── fixtures/
│   └── marcus_contracts/data/
└── results/
```

---

## Neo4j-Specific Gotchas

- **Aura Free**: 512MB heap, no GDS, no APOC. Stay under ~100K nodes.
- **Cypher 25 pragma**: all generated Cypher must start with `CYPHER 25`
- **MERGE order**: MERGE all node types before any relationship MERGE
- **Batch size**: 500 rows per `UNWIND $rows` — larger batches cause memory pressure on Aura Free
- **neo4j>=6.0.0**: package is `neo4j` not `neo4j-driver`; add `neo4j-rust-ext` alongside it
- **Docker startup**: wait ≥20s after `docker run` before connecting
- **GDS on Aura Free**: not available — check before generating GDS queries
- **MCP tool names**: `get-schema`, `read-cypher`, `write-cypher`, `list-gds-procedures`
- **reset.cypher**: always generate — enables clean re-runs without reprovisioning
