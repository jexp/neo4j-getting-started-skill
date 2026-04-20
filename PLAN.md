# PLAN.md — neo4j-getting-started-skill

**Goal**: Build a Claude Code skill that takes a user or agent from zero to a running Neo4j application in ≤15 min (autonomous) / ≤90 min (HITL).

**Status key**: `pending` | `in_progress` | `done` | `blocked`

---

## Phase 0 — Foundation

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 010 | 10 | `done` | Research existing resources | neo4j-skills, aura-onboarding-assistant, mcp-neo4j, GraphAcademy |
| 020 | 10 | `done` | Write neo4j-getting-started-research.md | Living reference doc |
| 030 | 10 | `done` | Write PLAN.md | |
| 040 | 10 | `done` | Set up skill directory structure | neo4j-getting-started-skill/ subfolder mirrors neo4j-skills |
| 050 | 10 | `done` | Write AGENTS.md | Conventions, gotchas, test commands |

## Phase 1 — SKILL.md Orchestrator + Named Stages

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 110 | 10 | `done` | SKILL.md — slim orchestrator (160 lines) | 8 named stages, 7 success gates, fast paths, HITL/autonomous modes |
| 120 | 10 | `done` | Stage 0: `prerequisites` reference | neo4j-mcp binary check + install, .gitignore |
| 121 | 10 | `done` | Stage 1: `context` reference | User interview, defaults, EXEC_METHOD detection |
| 122 | 10 | `done` | Stage 2: `provision` reference | Aura REST API + aura-cli + Docker |
| 123 | 10 | `done` | Stage 3: `model` reference | CSV-first, greenfield, demo, existing DB introspection |
| 124 | 10 | `done` | Stage 4: `load` reference | Preferred: Python batch via DataFrame + `$rows`; Northwind HTTPS example; neo4j-rust-ext |
| 125 | 10 | `done` | Stage 5: `explore` reference | Browser URL, notebook viz, VS Code extension |
| 126 | 10 | `done` | Stage 6: `query` reference | Query types, GDS guard, validation |
| 127 | 10 | `done` | Stage 7: `build` reference | Notebook, Streamlit, FastAPI, GraphRAG, MCP |

## Phase 2 — Shared Capability References

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 210 | 10 | `done` | capabilities/execute-cypher.md | 3 options: MCP, cypher-shell, Query API HTTP; EXEC_METHOD pattern |
| 220 | 10 | `done` | capabilities/mcp-config.md | neo4j-mcp config for Claude Desktop, Claude Code; read-only mode |
| 230 | 10 | `done` | capabilities/cypher-authoring.md | Min rules + pointer to neo4j-cypher-authoring-skill + validated pitfalls table |
| 240 | 8 | `pending` | domain-patterns.md — expand remaining domains | logistics, media; expand social/ecommerce/finance with more queries |
| 250 | 7 | `done` | Aura API — minimal endpoints in provision.md + OpenAPI spec pointer | No static reference file; agents discover additional endpoints from live spec |

## Phase 3 — Test Personas (5 total)

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 310 | 9 | `done` | Persona 1: alex_beginner.yml | Social, Aura Free, synthetic, notebook |
| 320 | 9 | `done` | Persona 2: sam_developer.yml | E-commerce, CSV, FastAPI + MCP |
| 330 | 7 | `pending` | Persona 3: jordan_ai_engineer.yml | RAG/KG, Docker + Aura, LangChain GraphRAG |
| 340 | 6 | `pending` | Persona 4: morgan_analyst.yml | Fraud detection, Aura Pro, Streamlit |
| 350 | 6 | `pending` | Persona 5: riley_platform_engineer.yml | SaaS, multi-instance, CI/CD |

## Phase 4 — Test Harness

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 410 | 9 | `done` | harness/runner.py scaffold | Invokes Claude with skill + persona, captures outputs |
| 420 | 9 | `done` | harness/validator.py scaffold | 7-gate validation pipeline |
| 430 | 8 | `pending` | harness/reporter.py | Markdown report: gate results, timing, diffs |
| 440 | 8 | `done` | Makefile — install/uninstall/integration/fixture targets | |
| 450 | 7 | `pending` | Update persona YAMLs for 7-gate model | Add graph_visible, update query gate to require ≥2 traversals |

## Phase 5 — Manual Testing & Iteration

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 510 | 10 | `pending` | Manual test: Persona 1 (Alex) end-to-end | `claude --append-system-prompt SKILL.md`, measure time, note gaps |
| 520 | 9 | `pending` | Manual test: Persona 2 (Sam) end-to-end | Needs CSV files (generate synthetic CSVs first) |
| 530 | 8 | `pending` | Fix skill based on manual test findings | |
| 540 | 8 | `pending` | Run automated harness: Persona 1 + 2 | Docker local for CI, Aura for full-path test |
| 550 | 7 | `pending` | Iterate to ≥70% gate pass rate on 2 personas | Target for initial ship |

## Phase 5b — Cypher & Load Validation (completed 2026-04-20)

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 560 | 10 | `done` | validate_cypher.py — EXPLAIN + direct execution harness | 54 pass / 7 skipped (templates) / 0 fail |
| 561 | 10 | `done` | Fix `--` → `//` comments in Cypher blocks | 5-explore.md, domain-patterns.md, cypher-authoring.md |
| 562 | 10 | `done` | Fix vector index OPTIONS backtick keys | 3-model.md, kg-from-documents.md, domain-patterns.md |
| 563 | 10 | `done` | Fix `[:REL*0..5]` → QPP `(()-[:REL]->()){0,5}` | domain-patterns.md IoT blast-radius query |
| 564 | 10 | `done` | Replace `db.index.vector.queryNodes()` with `SEARCH` clause | cypher-authoring.md, 6-query.md, domain-patterns.md |
| 565 | 10 | `done` | Preferred load pattern: DataFrame + `$rows` batch | 4-load.md rewritten; Northwind HTTPS example; validated against live DB |
| 566 | 10 | `done` | neo4j-rust-ext: import removed, PyPI dep only | All references updated; `neo4j-rust-ext` in requirements replaces `neo4j` |
| 567 | 10 | `done` | Document `CALL {} IN TRANSACTIONS` needs session.run() | cypher-authoring.md pitfalls table; validated in test_load_scripts.py |
| 568 | 9  | `done` | Stage file numeric prefixes (0-prerequisites.md … 7-build.md) | All references in SKILL.md updated |

## Phase 5c — Integration Harness & Progress Tracking (completed 2026-04-20)

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 570 | 10 | `done` | runner.py — temp work dir isolation | Each run in fresh tempdir; no source pollution |
| 571 | 10 | `done` | runner.py — skill install/uninstall lifecycle | install before, uninstall in finally block |
| 572 | 10 | `done` | runner.py — live streaming via stream-json | assistant/tool_use/result event parsing; break on result |
| 573 | 10 | `done` | runner.py — hang fix (break on result event + pipe close) | Closes pipes after proc.wait() to unblock streaming threads |
| 574 | 10 | `done` | runner.py — fixture injection via --fixture DIR | Copies files into work dir; patches __NEO4J_URI__ placeholder |
| 575 | 10 | `done` | Aura API — correct endpoints and JSON body | /oauth/token JSON; v2beta1 org/project; v1beta5 instances |
| 576 | 10 | `done` | aura.env / .env separation | API creds vs DB creds; dotenv_values; PROJECT_ID/ORG_ID optional |
| 577 | 9  | `done` | progress.md per-stage tracking | SKILL.md startup/resume protocol; ### headers per stage; On Completion sections in all 8 stage files |
| 578 | 9  | `done` | Fixture: alex_after_load | progress.md (stages 0-4 done), schema.json, schema.cypher |
| 579 | 9  | `done` | validate_cypher.py — filtered stderr (4 codes only) | _FilteredStderr class; UnknownPropertyKey/Label/RelType/ParameterNotProvided |
| 580 | 9  | `done` | Cypher: CALL {} IN TRANSACTIONS batching fix | UNWIND before CALL, not inside; cleanup: MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS |

## Phase 6 — Phase 2 Features (post-ship)

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 610 | 6 | `pending` | GraphRAG sub-skill | Separate `neo4j-graphrag-skill` folder; branch in stage 4/build for now |
| 620 | 6 | `pending` | JavaScript / Node.js path in `build` | App templates for JS |
| 630 | 6 | `pending` | APOC/GDS availability gating in `query` | Check plugins before generating GDS queries; Aura Free has no GDS |
| 640 | 6 | `pending` | GraphAcademy course links personalized | By EXPERIENCE + APP_TYPE + LANGUAGE |
| 650 | 5 | `pending` | Autoresearch loop setup | Target: maximize gate pass rate across 5 personas |
| 660 | 5 | `pending` | LLM judge for app_generated gate | Validate app actually answers use-case question, not just compiles |
| 670 | 5 | `pending` | Docker CI mode for harness | --db-mode=docker fast path; Aura mode for full-path tests |
| 680 | 5 | `pending` | Sub-skills: cypher-authoring, data-modeling, app-dev | Separate skill folders; skill can delegate to them; reusable outside this skill |
| 690 | 4 | `pending` | 2nd free DB for integration testing | Phase 2: keep main DB clean; run harness against separate instance |
| 700 | 6 | `pending` | Parallel provisioning — overlap model design with DB spin-up | After calling provision script, start stage 3-model while polling for DB readiness; apply schema + load once up — could recover ~60s of the ~260s provision wait |
| 710 | 5 | `pending` | Graph Type Schema support (preview) | Use `CREATE TYPE` / `RELATIONSHIP TYPE` DDL when DB supports it (≥Neo4j 5.x preview); detect support before generating schema.cypher; see https://neo4j.com/blog/developer/graph-type-schema-enforcement-made-easy-preview/ |

## Phase 7 — Integration & Ship

| ID | Priority | Status | Step | Notes |
|----|----------|--------|------|-------|
| 710 | 7 | `pending` | PR to neo4j-skills repo | Merge neo4j-getting-started-skill/ subfolder |
| 720 | 6 | `done` | README.md for repo root + skill folder | Installation, usage, integration testing, assumptions |
| 730 | 5 | `pending` | GraphAcademy alignment doc | Map stages to courses |

---

## Strategic Context

This skill replaces the `aura-onboarding-assistant` React SPA prototype (which explored agentic onboarding inside the platform). The goal is an equivalent CLI/agent-native experience: same user journey, no platform dependency, works with any Claude Code setup.

Target audience: both human developers (HITL, conversational) and autonomous agents (CI-like, `--auto-approve`). The skill must detect and adapt to both modes.

Shippable bar: 2 personas at 70% gate pass rate. Skill is "live" as soon as the branch is pushed.

---

## Key Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-20 | Stage names: prerequisites/context/provision/model/load/explore/query/build | Meaningful, agent-readable, ordered |
| 2026-04-20 | SKILL.md = thin orchestrator; detail in references/ | Avoids 700-line system prompt; agent reads only active stage |
| 2026-04-20 | Shared capabilities in references/capabilities/ | DRY — execute-cypher, mcp-config, cypher-authoring reused across stages |
| 2026-04-20 | EXEC_METHOD detected in `context`, used by all stages | One detection, consistent execution throughout |
| 2026-04-20 | Aura REST API directly (not mcp-neo4j-cloud-aura-api) | Direct curl needs no extra MCP server; simpler, fewer deps |
| 2026-04-20 | neo4j-rust-ext as PyPI dep only, no import | Drop-in replacement; just listing in requirements.txt is sufficient |
| 2026-04-20 | Preferred load = DataFrame + $rows batches | Works on Aura (no file:// access); any data source via pandas |
| 2026-04-20 | SEARCH clause replaces db.index.vector.queryNodes | Neo4j 2026.01+ native Cypher; old procedure still works but deprecated |
| 2026-04-20 | QPP replaces *min..max variable-length paths | CYPHER 25 standard; `(()-[:R]->()){0,5}` is the correct form |
| 2026-04-20 | CALL {} IN TRANSACTIONS needs session.run() | execute_query uses managed transaction which rejects this clause |
| 2026-04-20 | 15-min budget starts after DB RUNNING | Provisioning wait (1-3 min) doesn't count against it |
| 2026-04-20 | Graph visibility = hard success gate | "It clicks" moment required, not optional |
| 2026-04-20 | Query gate: ≥2 traversal queries | Count-only queries don't prove the graph model works |
| 2026-04-20 | Python-only for v1 | Focus quality; JS in phase 2 |
| 2026-04-20 | 2 personas at 70% gate pass = shippable | Pragmatic; skill is live in repo as soon as branch is pushed |
| 2026-04-20 | GraphRAG = branch in this skill, not separate | Separate neo4j-graphrag-skill planned for phase 2; minimal branch in stage 4/build for now |
| 2026-04-20 | graph_visible is a hard success gate | Seeing nodes+edges rendered is the "it clicks" moment for first-time graph users |
| 2026-04-20 | 15-min budget starts after DB running | Aura provisioning (1-3 min) doesn't count; use that time for model+data-prep work |
| 2026-04-20 | CSV-first modeling: inspect headers before designing | Data already exists → derive model from structure, not model-first |
| 2026-04-20 | reset.cypher always written | Dirty state recovery: re-run import without recreating the DB |
| 2026-04-20 | aura.env separate from .env | Writing .env during provision must never overwrite API credentials |
