# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3
NEO4J_MCP=/Users/mh/bin/neo4j-mcp

### 1-context
status: done
MODE=autonomous
DOMAIN=healthcare
USE_CASE=patient journey analysis — tracking encounters, diagnoses, and care gaps across providers
EXPERIENCE=intermediate
DB_TARGET=local-docker
DATA_SOURCE=synthetic
APP_TYPE=notebook
EXEC_METHOD=cypher-shell

### 2-provision
status: done
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j

### 3-model
status: done
labels=Patient,Encounter,Condition,Provider,Organization,Medication,CareGap
relationships=HAD_ENCOUNTER,WITH_PROVIDER,AT_ORGANIZATION,DIAGNOSED,PRESCRIBED,REFERRED_TO,HAS_CONDITION,WORKS_AT,HAS_CARE_GAP
constraints=7
files=schema/schema.json,schema/schema.cypher

### 4-load
status: done
nodes=502 Encounter, 100 Patient, 78 CareGap, 20 Provider, 15 Condition, 15 Medication, 10 Organization
relationships=861 DIAGNOSED, 502 HAD_ENCOUNTER, 502 WITH_PROVIDER, 502 AT_ORGANIZATION, 473 PRESCRIBED, 257 HAS_CONDITION, 78 HAS_CARE_GAP, 72 REFERRED_TO, 20 WORKS_AT
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=pat0001

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%3A%2F%2Fneo4j%40localhost%3A7687
viz_method=browser+notebook-neo4j-viz

### 6-query
status: done
queries_total=10
traversal_queries=7
queries_returning_rows=8
files=queries/queries.cypher

### 7-build
status: done
artifact=notebook.ipynb
app_type=notebook
run_command=jupyter notebook notebook.ipynb
files=notebook.ipynb,requirements.txt
