# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3.14
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
REGION_HINT=europe-west

### 2-provision
status: done
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
CONTAINER_NAME=neo4j-elena-test

### 3-model
status: done
labels=Patient,Provider,Encounter,Diagnosis,Medication
relationships=HAD_ENCOUNTER,WITH_PROVIDER,RESULTED_IN_DIAGNOSIS,PRESCRIBED,GENERATED_REFERRAL,HAS_ACTIVE_DIAGNOSIS
constraints=5
files=schema/schema.json,schema/schema.cypher
sample_id=p001

### 4-load
status: done
nodes=120 Patient, 15 Provider, 630 Encounter, 15 Diagnosis, 15 Medication
relationships=630 HAD_ENCOUNTER, 630 WITH_PROVIDER, 681 RESULTED_IN_DIAGNOSIS, 472 PRESCRIBED, 40 GENERATED_REFERRAL, 305 HAS_ACTIVE_DIAGNOSIS
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=p001

### 5-explore
status: done
browser_url=http://localhost:7474
browser_url_web=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40localhost%3A7687
viz_method=browser+notebook-neo4j-viz

### 6-query
status: done
queries_total=10
traversal_queries=8
queries_returning_rows=10
files=queries/queries.cypher

### 7-build
status: done
artifact=notebook.ipynb
app_type=notebook
run_command=jupyter notebook notebook.ipynb
files=notebook.ipynb,requirements.txt
