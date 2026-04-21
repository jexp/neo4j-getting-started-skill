# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3.13
NEO4J_MCP=/Users/mh/bin/neo4j-mcp
VENV=.venv

### 1-context
status: done
MODE=autonomous
DOMAIN=social
USE_CASE=friend recommendations and community discovery
EXPERIENCE=beginner
DB_TARGET=aura-free
DATA_SOURCE=synthetic
APP_TYPE=notebook
EXEC_METHOD=cypher-shell
CLOUD_PROVIDER=gcp
REGION_HINT=europe-west

### 2-provision
status: done
NEO4J_URI=neo4j+s://376be46b.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=376be46b
files=scripts/provision_aura.py

### 3-model
status: done
labels=Person,Post,Hashtag,Community
relationships=FOLLOWS,POSTED,LIKED,TAGGED,MEMBER_OF
constraints=4
files=schema/schema.json,schema/schema.cypher
sample_id=p1

### 4-load
status: done
nodes=200 Person,100 Post,20 Hashtag,10 Community
relationships=2800 FOLLOWS,780 LIKED,269 MEMBER_OF,197 TAGGED,100 POSTED
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=p1

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40376be46b.databases.neo4j.io
viz_method=browser+notebook-neo4j-viz

### 6-query
status: done
queries_total=12
traversal_queries=8
queries_returning_rows=6
files=queries/queries.cypher

### 7-build
status: done
artifact=notebook.ipynb
app_type=notebook
run_command=.venv/bin/jupyter notebook notebook.ipynb
files=notebook.ipynb,requirements.txt
