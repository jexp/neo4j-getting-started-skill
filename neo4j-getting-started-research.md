# Neo4j Getting-Started Skill — Research Document

**Created**: 2026-04-20  
**Status**: Living document — update as new resources discovered

---

## 1. The Problem: Agentic Onboarding

Traditional onboarding is a UI/docs flow. In the age of agentic engineering, the onboarding *is* a skill — a reusable, composable, automatable sequence that both humans-with-agents and pure-autonomous-agents can execute to reach "zero to success" with a graph database.

**Key insight from the discussion**: Builder agents (Cursor, Claude Code, Windsurf, etc.) should be able to execute the same journey as in-product UI flows — via MCP, aura-cli, APIs, and code generation. The skill is both a test bed and a product.

**Target success state** (defined by user):
1. Running Neo4j database (Aura or local Desktop)
2. Suitable data model for their use-case
3. Data imported (synthetic or real)
4. Cypher queries returning useful insights
5. Dashboard / notebook / application running against the DB
6. Database integrated into agent framework via MCP or other integration
7. Time budget: ≤15 min autonomous, ≤90 min HITL

---

## 2. The Five Stages of the User Journey

### Stage 1: Database Provisioning (`db`)
**Goal**: Have a running, accessible Neo4j database

**Aura path**:
- `aura-cli instance create` — provision AuraDB Free/Pro
- API: `POST /v1/instances` via `mcp-neo4j-cloud-aura-api`
- Aura Console: https://console.neo4j.io
- Credentials: Client ID + Secret → stored in `~/.aura/config`

**Local Desktop path**:
- Neo4j Desktop download + project creation
- `neo4j-admin server start` (Community/Enterprise)
- Docker: `docker run -p 7474:7474 -p 7687:7687 neo4j:latest`

**Key parameters to collect from user**:
- Cloud provider (GCP/AWS/Azure) or local
- Region (auto-detect from IP or ask)
- Instance size (Free=512MB, Pro=1GB+)
- Plugins needed: GDS, GenAI, APOC

**MCP tool**: `mcp-neo4j-cloud-aura-api` → `create_instance`
**CLI tool**: `aura-cli instance create --name <n> --cloud-provider <p> --region <r> --type free-db`

---

### Stage 2: Data Modeling (`model`)
**Goal**: A graph schema suited to the user's domain and use-case

**Inputs from user**:
- Domain/industry (e.g., e-commerce, healthcare, social network, finance)
- Use-case (e.g., recommendations, fraud detection, knowledge graph, RAG)
- Existing data sources (CSV, PostgreSQL, JSON, API)
- Optional: existing ER diagram or schema description

**Outputs**:
- Node labels with key properties
- Relationship types with direction and properties
- Arrows.app-compatible JSON (importable/exportable)
- Cypher DDL: constraints + indexes

**Tools**:
- `mcp-neo4j-data-modeling` server: `validate_data_model`, `visualize_data_model`, `export_to_arrows_json`
- LLM generation via `neo4j-cypher-authoring-skill` for DDL
- Arrows.app: https://arrows.app for visual editing, export to JSON

**GraphAcademy course**: *Graph Data Modeling Fundamentals* (2 hours)

**Reference patterns by domain**:
- Social: (Person)-[:FOLLOWS]->(Person), (Person)-[:POSTED]->(Post)
- E-commerce: (Customer)-[:PURCHASED]->(Product), (Order)-[:CONTAINS]->(Product)  
- Finance: (Account)-[:TRANSFERRED_TO {amount}]->(Account), (Transaction)-[:USED]->(Card)
- Knowledge Graph: (Entity)-[:MENTIONS]->(Entity), (Document)-[:HAS_CHUNK]->(Chunk)
- RAG/GraphRAG: (Article)-[:HAS_CHUNK]->(Chunk), (Chunk)-[:MENTIONS]->(Entity)

---

### Stage 3: Data Import (`import`)
**Goal**: Data loaded into the database, ready to query

**Sub-paths**:

#### A. Synthetic data generation
- LLM generates Cypher `CREATE`/`MERGE` statements matching the model
- Or: LLM generates CSV files → `LOAD CSV` import
- Best for: demos, prototypes, learning

#### B. CSV/flat file import
- `LOAD CSV WITH HEADERS FROM 'file:///...' AS row`
- `neo4j-admin database import` for bulk (offline)
- Aura Data Importer (UI): drag-and-drop CSV → visual mapping

#### C. Relational database migration
- `neo4j-admin database import` (from CSV exports)
- APOC's `apoc.load.jdbc` for live relational import
- ETL tools: Kettle, Talend

#### D. API/streaming
- APOC: `apoc.load.json`, `apoc.load.xml`
- Custom Python/JS scripts using neo4j driver

**Tools**:
- `neo4j-mcp` official binary: Cypher write for batch CREATE/MERGE
- `neo4j-admin-reference.md`: bulk import commands
- Aura Data Importer API (in aura-onboarding-assistant mock)

**GraphAcademy course**: *Importing Data Fundamentals* (2 hours)

---

### Stage 4: Query & Insight (`query`)
**Goal**: Cypher queries returning meaningful results from the user's data

**Types of queries to generate**:
- Basic: node count, property exploration, list top-N entities
- Traversal: find connected entities, path finding, neighborhood
- Aggregation: group by, count, sum, avg, distribution
- Advanced: subgraphs, pattern matching, temporal, geo
- GenAI: vector similarity search, fulltext search, GraphRAG

**Tools**:
- `neo4j-cypher-authoring-skill` for query generation
- `neo4j-mcp` official binary: execute queries and inspect schema


**Parameterization**: Generate queries with `$param` placeholders for reuse in apps/dashboards

**GraphAcademy courses**: *Cypher Fundamentals* (1h), *Sharpen your Cypher* track (7 courses)

---

### Stage 5: Application / Integration (`app`)
**Goal**: A running app, dashboard, or agent integration

**Output options** (ranked by complexity):

#### 5a. Cypher Notebook (Jupyter)
- Python: `neo4j` driver + `pandas` + `matplotlib`/`plotly`
- Lightest: just queries + visualizations

#### 5b. Streamlit App
- Python: `neo4j` driver + `streamlit`
- Interactive: sliders/filters → Cypher → graph/chart
- Fast to build, great for demos

#### 5c. FastAPI Backend
- Python FastAPI template (from `aura-onboarding-assistant/python-app-template/`)
- REST endpoints → Cypher queries → JSON responses
- OpenAPI spec auto-generated → usable in Salesforce, etc.

#### 5d. Node.js/Express Backend
- JavaScript template (from aura-onboarding-assistant)
- Same pattern as FastAPI

#### 5e. Aura Dashboard
- Via `mcp-neo4j-cloud-aura-api` or Explore (built-in)
- Charts: bar, pie, line, scatter from Cypher results

#### 5f. Agent/MCP Integration
- `neo4j-mcp` official binary → add to `claude_desktop_config.json` or `.claude/settings.json`
- Agent framework: LangChain, LlamaIndex, CrewAI, Mastra, ADK
- GraphRAG: `neo4j-graphrag` library with `HybridCypherRetriever`

**Templates available** (in aura-onboarding-assistant):
- Python FastAPI: `python-app-template/` — full template with env vars, Cypher endpoints
- JavaScript Express: `JavaScriptAppGenerator`
- Java Javalin: `JavaAppGenerator`

---

## 3. Available Tools & APIs

### MCP Servers (from mcp-neo4j/)
| Server | Key Tools | Use In Skill |
|--------|-----------|--------------|
| `neo4j-mcp` (official binary) | `cypher` (read/write), `schema` | Stages 3, 4, 5 |
| `mcp-neo4j-cloud-aura-api` | `create_instance`, `list_instances`, `pause_instance` | Stage 1 |
| `mcp-neo4j-data-modeling` | `validate_data_model`, `visualize_data_model`, `export/load_arrows_json` | Stage 2 |
| `mcp-neo4j-memory` | `create_entities`, `create_relations`, `query_entities` | Cross-cutting |

### CLI Tools (from neo4j-skills/neo4j-cli-tools-skill/)
| Tool | Key Commands | Use In Skill |
|------|-------------|--------------|
| `aura-cli` | `instance create/list/delete`, `credential add` | Stage 1 |
| `cypher-shell` | Interactive REPL, script execution | Stages 3, 4 |
| `neo4j-admin` | `database import`, `server start/stop` | Stages 1, 3 |

### APIs
- **Aura REST API**: `https://api.neo4j.io/v1/` — instance CRUD, tenant mgmt
- **Neo4j HTTP Transaction API**: `POST /db/{db}/tx/commit` — Cypher over HTTP (no Bolt)
- **GraphAcademy API**: Course progress tracking

### Libraries
- **Python**: `neo4j>=6.0.0` (driver), `neo4j-graphrag` (GraphRAG), `langchain-neo4j`
- **JavaScript**: `neo4j-driver`, `@langchain/community`
- **Java**: `neo4j-java-driver`

---

## 4. Existing Resources to Leverage

### neo4j-skills/ repo
- `neo4j-cli-tools-skill/` — CLI reference, aura-cli deep docs → Stage 1
- `neo4j-cypher-authoring-skill/` — Cypher 25 generation → Stages 2, 4
- `neo4j-migration-skill/` — driver version guidance → Stage 5
- `skill-generation-validation-tools/` — test harness, persona YAML, validation pipeline

### aura-onboarding-assistant/
- `spec/spec.md` — 10-phase onboarding spec (most detailed single reference)
- `src/services/llm.service.ts` — LLM prompt patterns for schema, Cypher, dashboard gen
- `src/services/framework.service.ts` — Aura API mock patterns
- `python-app-template/` — FastAPI template for Stage 5

### aura-onboarding/ (Mastra agents version)
- Agent architecture: `ProfileCollectionAgent`, `AgentOrchestrator`
- MCP config: `neo4j-aura-manager`, `neo4j-cypher`, `neo4j-test-server`

### GraphAcademy Courses (learning path alignment)
| Stage | Course | Duration |
|-------|--------|----------|
| 1 | AuraDB Fundamentals | 1h |
| 1 | Neo4j Fundamentals | 1h |
| 2 | Graph Data Modeling Fundamentals | 2h |
| 3 | Importing Data Fundamentals | 2h |
| 4 | Cypher Fundamentals | 1h |
| 4+ | Sharpen your Cypher (7 courses) | varies |
| 5 | Build a Neo4j-backed Application (24 courses) | varies |
| 5 | Build a GraphRAG Personal Assistant | varies |
| 5 | MCP (2 courses) | varies |

### Agent Skills Ecosystem (neo4j labs)
- `neo4j-cypher-authoring-skill` — production-grade Cypher generation with 4-gate validation
- `neo4j-cli-tools-skill` — CLI operations
- `neo4j-migration-skill` — driver upgrades
- The **getting-started-skill** (this project) — orchestrates all above

---

## 5. User Input Collection Design

### Required inputs
```yaml
user:
  name: string
  company: string (optional)
  domain: enum[social, ecommerce, finance, healthcare, logistics, media, legal, iot, custom]
  use_case: string  # free text, e.g. "fraud detection", "product recommendations"
  experience: enum[beginner, intermediate, advanced]

infrastructure:
  target: enum[aura-free, aura-pro, local-desktop, local-docker, existing]
  cloud_provider: enum[gcp, aws, azure]  # only if aura
  
data:
  source: enum[synthetic, csv-upload, database, api, existing-neo4j]
  description: string  # "I have a CSV of transactions" or "I'll use synthetic data"

app:
  language: enum[python, javascript, java, none]
  framework: enum[fastapi, streamlit, express, spring, none]
  integration: enum[mcp, langchain, llamaindex, crewai, mastra, adk, none]
```

### Optional (advanced)
```yaml
  architecture:
    agent_framework: string
    cloud_provider: string
    vector_search: bool
    graph_data_science: bool
    graphrag: bool
```

---

## 6. Agentic Execution Architecture

### For autonomous coding agents (Claude Code, Cursor, Windsurf)
The skill executes via a structured protocol:

```
Phase 0: Collect inputs (AskUser or parse from context)
Phase 1: Provision DB (aura-cli OR mcp-neo4j-cloud-aura-api OR docker run)
Phase 2: Design model (LLM + mcp-neo4j-data-modeling validate/visualize)
Phase 3: Generate + import data (LLM Cypher + neo4j-mcp write)
Phase 4: Generate + run queries (neo4j-cypher-authoring-skill + neo4j-mcp read)
Phase 5: Generate app/integration (template fill + code gen)
```

### For in-product UI (Aura platform)
Same 5 phases but surfaced through UI components:
- `aura-onboarding-assistant` React SPA
- `Neo4jAuraFramework` mocked API calls
- NVL graph visualization

### Shared protocol
Both paths share the same **decision tree** and **content generation** logic — only the execution layer differs (MCP tools vs UI components vs API calls).

---

## 7. Test Personas (2 → 5)

### Persona 1: The Curious Beginner ("Alex")
- **Domain**: Social network / personal project
- **Experience**: Beginner, first graph DB
- **Target**: Aura Free, no existing data
- **Data**: Synthetic friend network
- **App**: Python notebook
- **Integration**: None
- **Success criteria**: DB running, model visible, 5 queries working, notebook renders graph

### Persona 2: The Pragmatic Developer ("Sam")
- **Domain**: E-commerce
- **Experience**: Intermediate, knows SQL
- **Target**: Aura Pro, has CSV files (products, orders, customers)
- **Data**: Real CSV import
- **App**: FastAPI backend + basic HTML frontend
- **Integration**: MCP for Claude Desktop
- **Success criteria**: CSV imported, recommendation queries working, API running, MCP connected

### Persona 3: The AI/ML Engineer ("Jordan")
- **Domain**: Knowledge graph / RAG
- **Experience**: Advanced, knows Python/LLMs
- **Target**: Local Docker (dev), Aura Pro (prod)
- **Data**: Documents → chunked + embedded
- **App**: LangChain agent with GraphRAG
- **Integration**: MCP + LangChain `Neo4jGraph`
- **Success criteria**: GraphRAG pipeline working, HybridCypherRetriever configured, agent answering multi-hop questions

### Persona 4: The Enterprise Analyst ("Morgan")
- **Domain**: Financial fraud detection
- **Experience**: Intermediate, BI background
- **Target**: Aura Pro (enterprise team)
- **Data**: Existing PostgreSQL (transactions, accounts)
- **App**: Streamlit dashboard with real-time fraud alerts
- **Integration**: None initially, MCP later
- **Success criteria**: Fraud ring queries running, Streamlit dashboard deployed, < 30min total

### Persona 5: The Platform Engineer ("Riley")
- **Domain**: Multi-tenant SaaS graph
- **Experience**: Advanced, DevOps background
- **Target**: Aura Enterprise, multiple instances
- **Data**: API-sourced (REST → Neo4j)
- **App**: Node.js microservice + CI/CD pipeline
- **Integration**: All MCPs configured, agent framework (CrewAI)
- **Success criteria**: Multi-instance management working, full pipeline automated, < 15min autonomous

---

## 8. Auto-Testing Strategy

### Harness design (extending neo4j-skills test harness)
```yaml
# persona-test-case format
persona: alex_beginner
inputs:
  domain: social
  use_case: "friend recommendations"
  experience: beginner
  target: aura-free
  data: synthetic
  language: python
  framework: notebook
  integration: none

success_gates:
  - gate: db_running
    check: driver.verify_connectivity()
  - gate: model_valid
    check: schema has ≥2 node labels, ≥1 relationship type
  - gate: data_present
    check: MATCH (n) RETURN count(n) > 0
  - gate: queries_run
    check: all 5 generated queries return ≥1 result
  - gate: app_generated
    check: generated file exists, runs without syntax error
  - gate: time_budget
    check: total_seconds < 900  # 15 min
```

### Running the skill as a test
```bash
# Invoke Claude Code with the skill appended
claude --append-system-prompt neo4j-getting-started-skill/SKILL.md \
       --persona tests/personas/alex_beginner.yml \
       --auto-approve
```

---

## 9. Key Technical Decisions

### Skill format: follows neo4j-skills conventions
- `neo4j-getting-started-skill/SKILL.md` — main skill file
- `neo4j-getting-started-skill/references/` — stage-specific references
- `neo4j-getting-started-skill/tests/personas/` — persona YAML files
- `neo4j-getting-started-skill/tests/harness/` — runner + validator

### Skill invocation model
The skill is a **SYSTEM PROMPT EXTENSION** — it adds orchestration protocol to any coding agent. The agent uses the tools it already has (Bash, WebFetch, Edit, Write) plus whichever MCP servers are configured.

### Compatibility
- Claude Code (primary target)
- Cursor (MCP support via `.cursor/mcp.json`)
- Any agent supporting `--system-prompt` injection

### Tool dependencies
- Minimum: Bash (for aura-cli, docker, cypher-shell)
- Recommended: `neo4j-mcp` (official binary), `mcp-neo4j-cloud-aura-api`, `mcp-neo4j-data-modeling`
- Optional: `mcp-neo4j-memory` (cross-session state)

---

## 10. Open Questions / Decisions Needed

1. **GraphAcademy API**: Can we programmatically query courses by persona/track to recommend the right learning path inline?
2. **Aura Free vs Pro detection**: Should the skill auto-select Free for beginners and guide upgrades?
3. **Local Docker fallback**: Should the skill offer `docker run neo4j` as a fallback when no Aura credentials exist?
4. **Data modeling server**: Is `mcp-neo4j-data-modeling` (from mcp-neo4j/) production-ready and installed by default?
5. **Arrows.app integration**: Can we generate Arrows.app URLs programmatically for visualization?
6. **Persona auto-detection**: Can the skill infer persona from git repo context (package.json, requirements.txt, existing code)?
7. **Multi-language app templates**: Priority order for additional languages beyond Python/JS?
8. **Progress persistence**: Use `mcp-neo4j-memory` to checkpoint progress across sessions?
9. **HITL checkpoints**: Which stages require human confirmation (model review, data preview, query validation)?

---

## 11. References

- `neo4j-skills/` repo: `/Users/mh/d/llm/neo4j-skills/`
- `aura-onboarding-assistant/` spec: `/Users/mh/d/llm/aura-onboarding-assistant/spec/spec.md`
- `mcp-neo4j/` servers: `/Users/mh/d/llm/mcp-neo4j/servers/`
- `aura-cli-reference.md`: `/Users/mh/d/llm/neo4j-skills/neo4j-cli-tools-skill/references/aura-cli-reference.md`
- GraphAcademy: https://graphacademy.neo4j.com/categories/
- Arrows.app: https://arrows.app
- Aura Console: https://console.neo4j.io
- Neo4j Desktop: https://neo4j.com/download/
