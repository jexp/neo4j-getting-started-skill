# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3.13
NEO4J_MCP=/Users/mh/bin/neo4j-mcp

### 1-context
status: done
MODE=autonomous
DOMAIN=ecommerce
USE_CASE=product recommendations and customer behavior analysis
EXPERIENCE=intermediate
DB_TARGET=aura-pro
DATA_SOURCE=csv
APP_TYPE=fastapi
INTEGRATION=mcp
LANGUAGE=python
EXEC_METHOD=cypher-shell

### 2-provision
status: done
NEO4J_URI=neo4j+s://1931831c.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=1931831c
files=scripts/provision_aura.py

### 3-model
status: done
labels=Customer,Product,Category,Order,Review
relationships=PLACED,CONTAINS,VIEWED,WROTE,REVIEWS,BELONGS_TO,SUBCATEGORY_OF
constraints=5
files=schema/schema.json,schema/schema.cypher
sample_id=cust0001

### 4-load
status: done
nodes=200 Customer, 502 Order, 199 Review, 30 Product, 10 Category
relationships=1833 VIEWED, 1271 CONTAINS, 502 PLACED, 199 WROTE, 199 REVIEWS, 30 BELONGS_TO, 5 SUBCATEGORY_OF
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=cust0001

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%401931831c.databases.neo4j.io
viz_method=browser

### 6-query
status: done
queries_total=14
traversal_queries=10
queries_returning_rows=14
files=queries/queries.cypher

### 7-build
status: done
artifact=main.py
app_type=fastapi+mcp
run_command=uvicorn main:app --reload
files=main.py,requirements.txt,mcp-claude-code.json,mcp-claude-desktop.json
