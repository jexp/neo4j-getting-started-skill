# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3
NEO4J_MCP=/Users/mh/bin/neo4j-mcp

### 2-provision
status: done
NEO4J_URI=neo4j+s://2ba515de.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=2ba515de
files=scripts/provision_aura.py

### 7-build
status: done
artifact=app.py
app_type=streamlit
run_command=streamlit run app.py
files=app.py,requirements.txt

### 6-query
status: done
queries_total=10
traversal_queries=6
queries_returning_rows=6
files=queries/queries.cypher

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%402ba515de.databases.neo4j.io
viz_method=browser

### 4-load
status: done
nodes=753 Transaction, 253 Account, 80 Person, 60 IP, 50 Device
relationships=753 INITIATED, 753 CREDITED_TO, 381 LOGGED_IN_FROM, 378 ACCESSED_FROM, 253 OWNS
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=acc00001

### 3-model
status: done
labels=Account,Transaction,Person,Device,IP
relationships=OWNS,INITIATED,CREDITED_TO,LOGGED_IN_FROM,ACCESSED_FROM,FLAGGED_BY
constraints=5
files=schema/schema.json,schema/schema.cypher
sample_id=acc00001

### 1-context
status: done
MODE=autonomous
DOMAIN=financial services
USE_CASE=transaction fraud ring detection and suspicious account network analysis
EXPERIENCE=intermediate
DB_TARGET=aura-free
DATA_SOURCE=synthetic
APP_TYPE=streamlit
EXEC_METHOD=mcp
REGION_HINT=europe-west
