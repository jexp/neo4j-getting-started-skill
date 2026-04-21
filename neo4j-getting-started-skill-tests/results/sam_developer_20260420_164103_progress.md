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
APP_TYPE=fastapi,mcp
EXEC_METHOD=cypher-shell
CLOUD_PROVIDER=aws
REGION_HINT=europe-west

### 3-model
status: done
labels=Customer,Product,Category,Order
relationships=PLACED,CONTAINS,IN_CATEGORY
constraints=4
files=schema/schema.json,schema/schema.cypher
sample_id=cust1

### 6-query
status: done
queries_total=10
traversal_queries=8
queries_returning_rows=10
files=queries/queries.cypher

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40b82b5aa3.databases.neo4j.io
viz_method=browser

### 2-provision
status: done
NEO4J_URI=neo4j+s://b82b5aa3.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=b82b5aa3
files=scripts/provision_aura.py

### 4-load
status: done
nodes=150 Customer, 46 Product, 8 Category, 300 Order
relationships=300 PLACED, 898 CONTAINS, 46 IN_CATEGORY
files=data/import.py,schema/reset.cypher
sample_id=cust1
