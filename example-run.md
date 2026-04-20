# Example Run — Alex Beginner Persona

Annotated transcript of an autonomous integration test run.  
Persona: social network, friend recommendations, Aura Free, synthetic data, Python notebook.  
Result: **PASS 7/7 gates** in ~9 min, $1.26.

Credentials and instance IDs are redacted.

---

## Invocation

```
make integration-alex
```

Which runs:
```
python3 tests/harness/runner.py --persona tests/personas/alex_beginner.yml --verbose
```

Prompt injected:
```
I want to get started with Neo4j. Domain: social, use-case: friend recommendations
and community discovery, experience: beginner, database: aura-free, data: synthetic,
app: notebook in python, integration: none. Please guide me through the complete
getting-started process.
```

---

## Stage 0 — prerequisites (~18s)

Checks Python version, neo4j-mcp binary, writes `.gitignore`.

```
[+9s] ## Stage: 0-prerequisites — Verify and install required CLI tools

  [tool] Bash  which neo4j-mcp → /Users/.../bin/neo4j-mcp  FOUND
  [tool] Bash  python3.13 --version → Python 3.13.5
  [tool] Bash  add .env aura.env neo4j-mcp to .gitignore
  [tool] Write progress.md  (stage 0 done)

[+40s] ## Stage: 1-context — Collect use-case variables
```

`progress.md` after stage 0–1:
```markdown
### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3.13

### 1-context
status: done
DOMAIN=social
USE_CASE=friend recommendations and community discovery
EXPERIENCE=beginner
DB_TARGET=aura-free
DATA_SOURCE=synthetic
APP_TYPE=notebook
EXEC_METHOD=cypher-shell
```

---

## Stage 2 — provision (~260s, mostly Aura spin-up wait)

Reads `aura.env`, writes `scripts/provision_aura.py`, runs it, waits for instance.

```
[+58s] ## Stage: 2-provision — Provision an Aura Free database

  [tool] Bash  cat aura.env → CLIENT_ID and CLIENT_SECRET found
  [tool] Bash  mkdir -p scripts
  [tool] Write scripts/provision_aura.py  (21s to write)
  [tool] Bash  python3.13 scripts/provision_aura.py
               → Waiting for instance... (polls every 10s)
               → Instance running: neo4j+s://[REDACTED].databases.neo4j.io
  [tool] Bash  cypher-shell connectivity check → Connected ✓
  [tool] Edit  progress.md

[+318s] Database is live ✓

## Stage: 3-model — Design the graph data model
```

`progress.md` after provision:
```markdown
### 2-provision
status: done
NEO4J_URI=neo4j+s://[REDACTED].databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=[REDACTED]
files=scripts/provision_aura.py
```

---

## Stage 3 — model (~57s)

Reads `domain-patterns.md`, proposes model, writes schema files, applies DDL.

```
[+318s] ## Stage: 3-model — Design the graph data model

  [tool] Read  references/domain-patterns.md
```

Proposed model (auto-approved in autonomous mode):
```
Nodes:     Person {id, name, email, joinedAt, bio}
           Post {id, content, createdAt, likes}
           Hashtag {name}
           Community {id, name, description}

Relationships:
  (Person)-[:FOLLOWS]->(Person)
  (Person)-[:POSTED]->(Post)
  (Post)-[:TAGGED]->(Hashtag)
  (Person)-[:MEMBER_OF]->(Community)
  (Person)-[:LIKED]->(Post)
```

```
  [tool] Bash   mkdir -p schema data queries
  [tool] Write  schema/schema.json
  [tool] Write  schema/schema.cypher
  [tool] Bash   cypher-shell --file schema/schema.cypher → 4 constraints applied
  [tool] Edit   progress.md
```

`schema/schema.cypher`:
```cypher
CREATE CONSTRAINT person_id    IF NOT EXISTS FOR (p:Person)    REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT post_id      IF NOT EXISTS FOR (p:Post)      REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT hashtag_name IF NOT EXISTS FOR (h:Hashtag)   REQUIRE h.name IS UNIQUE;
CREATE CONSTRAINT community_id IF NOT EXISTS FOR (c:Community) REQUIRE c.id IS UNIQUE;
CREATE INDEX person_name       IF NOT EXISTS FOR (p:Person) ON (p.name);
CREATE INDEX post_created      IF NOT EXISTS FOR (p:Post)   ON (p.createdAt);
```

---

## Stage 4 — load (~105s)

Generates CSVs, imports via pandas DataFrame batches.

```
[+375s] ## Stage: 4-load — Generate and import synthetic data

  [tool] Bash   pip install neo4j pandas python-dotenv -q
  [tool] Write  data/generate.py   (7s)
  [tool] Write  data/import.py     (35s)
  [tool] Write  schema/reset.cypher
  [tool] Bash   python3 data/generate.py → 9 CSV files written
  [tool] Bash   python3 data/import.py   → 527 nodes, 4381 rels loaded
  [tool] Edit   progress.md
```

Files in `data/`:
```
persons.csv       200 rows    communities.csv   10 rows
posts.csv         300 rows    follows.csv     2310 rows
hashtags.csv       17 rows    likes.csv       1202 rows
memberships.csv   499 rows    tagged.csv       605 rows
```

`progress.md` after load:
```markdown
### 4-load
status: done
nodes=200 Person, 300 Post, 17 Hashtag, 10 Community
relationships=2310 FOLLOWS, 1202 LIKED, 605 TAGGED, 499 MEMBER_OF, 300 POSTED
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=p1
```

---

## Stage 5 — explore (~17s)

Constructs and prints Neo4j Browser URL.

```
[+480s] ## Stage: 5-explore — Visual entry point to the graph

  [tool] Bash  python3 -c "encode NEO4J_URI into browser URL"
  [tool] Edit  progress.md

[+497s] ## Your graph is alive!

Neo4j Browser:
https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40[REDACTED].databases.neo4j.io

Starter query:
  MATCH (p:Person)-[:FOLLOWS]->(friend:Person) RETURN p, friend LIMIT 50
```

---

## Stage 6 — query (~57s)

Writes 10-query library, validates all via `validate_queries.py`.

```
[+497s] ## Stage: 6-query — Build the Cypher query library

  [tool] Bash   cypher-shell "CALL gds.version()" → GDS not available on Aura Free
  [tool] Write  queries/queries.cypher  (10 queries, 6 traversals)
  [tool] Bash   python3 .../validate_queries.py
               → 10/10 passed  |  6 traversal queries  PASS
  [tool] Edit   progress.md
```

Sample queries from `queries/queries.cypher`:
```cypher
// Q3: Friend-of-friend recommendations
CYPHER 25
MATCH (me:Person {id: $personId})-[:FOLLOWS]->(f)-[:FOLLOWS]->(fof)
WHERE NOT exists { (me)-[:FOLLOWS]->(fof) } AND me <> fof
WITH fof, count(DISTINCT f) AS mutualFriends
ORDER BY mutualFriends DESC LIMIT 10
RETURN fof.name AS suggestion, mutualFriends;

// Q4: Top influencers
CYPHER 25
MATCH (p:Person)
RETURN p.name AS person,
       count { (p)<-[:FOLLOWS]-() } AS followers
ORDER BY followers DESC LIMIT 20;
```

---

## Stage 7 — build (~120s)

Smoke-tests key query, then composes 22-cell notebook.

```
[+554s] ## Stage: 7-build — Generate the Python notebook

  [tool] Bash   python3 smoke-test: driver.verify_connectivity() + recommendation query
               → ✓ Connected  ✓ 10 recommendations returned
  [tool] Write  notebook.ipynb  (76s — 22 cells)
  [tool] Bash   python3 -m json.tool notebook.ipynb → ✓ Valid notebook JSON
  [tool] Write  requirements.txt
  [tool] Edit   progress.md
```

Notebook structure:
```
Cell 1  [md]   Title + introduction
Cell 2  [code] %pip install (commented out)
Cell 3  [code] Imports + load_dotenv
Cell 4  [code] Connect to Neo4j, define run()
Cell 5  [md]   What's in the graph?
Cell 6  [code] Node counts by label
Cell 7  [code] Relationship counts by type
...
Cell N  [code] Graph visualization (neo4j-viz)
Cell N  [code] Use-case answer + bar chart
Cell 22 [code] driver.close()
```

`requirements.txt`:
```
neo4j>=6.0.0
pandas>=2.0.0
python-dotenv>=1.0.0
jupyter>=1.0.0
ipykernel
matplotlib>=3.0.0
neo4j-viz>=1.0.0
```

---

## Gate results

```
============================================================
Persona: alex_beginner  [PASS]
Total time: 547.9s (~9 min)
Cost: $1.26
Gates: 7/7 passed
------------------------------------------------------------
  ✓ db_running      Connected successfully
  ✓ model_valid     4 labels, 5 relationship types
  ✓ data_present    527 nodes present
  ✓ queries_work    10/10 queries pass, 6 traversals
  ✓ graph_visible   Browser URL recorded
  ✓ app_generated   notebook.ipynb generated and valid
  ✓ time_budget     547.9s / 900s limit
============================================================
```

---

## Generated file tree

```
.env                          DB credentials (gitignored)
aura.env                      Aura API credentials (gitignored)
progress.md                   Stage-by-stage progress log
requirements.txt              Python dependencies
README.md                     This project's guide (generated)

schema/
  schema.json                 Graph model definition
  schema.cypher               Constraints + indexes (re-apply anytime)
  reset.cypher                Wipe data, keep schema

data/
  generate.py                 Synthetic data generator
  import.py                   CSV → Neo4j loader (applies schema first)
  persons.csv                 200 Person nodes
  posts.csv                   300 Post nodes
  hashtags.csv                17 Hashtag nodes
  communities.csv             10 Community nodes
  follows.csv                 2310 FOLLOWS relationships
  likes.csv                   1202 LIKED relationships
  memberships.csv             499 MEMBER_OF relationships
  tagged.csv                  605 TAGGED relationships

queries/
  queries.cypher              10-query library (validated)

scripts/
  provision_aura.py           Aura provisioning script

notebook.ipynb                22-cell Jupyter notebook
```
