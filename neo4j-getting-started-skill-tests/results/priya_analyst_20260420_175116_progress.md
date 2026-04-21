# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3.13
NEO4J_MCP=/Users/mh/bin/neo4j-mcp

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

### 2-provision
status: done
NEO4J_URI=neo4j+s://e4da2c15.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=e4da2c15
files=scripts/provision_aura.py

### 3-model
status: done
labels=Account,Transaction,Phone,Device,IPAddress
relationships=PERFORMS,BENEFITS_TO,USES_PHONE,VIA,FROM_IP
constraints=5
files=schema/schema.json,schema/schema.cypher
sample_id=acc_001

### 4-load
status: done
nodes=1310 Transaction, 200 Account, 60 Phone, 50 Device, 40 IPAddress
relationships=1316 VIA, 1310 PERFORMS, 1310 BENEFITS_TO, 794 FROM_IP, 200 USES_PHONE
files=data/generate.py,data/import.py,schema/reset.cypher

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40e4da2c15.databases.neo4j.io
viz_method=browser

### 6-query
status: done
queries_total=10
traversal_queries=6
queries_returning_rows=8
files=queries/queries.cypher

### 7-build
status: done
artifact=app.py
app_type=streamlit
run_command=streamlit run app.py
files=app.py,requirements.txt
