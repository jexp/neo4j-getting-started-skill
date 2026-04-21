# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=/opt/homebrew/bin/python3.13
NEO4J_MCP=/Users/mh/bin/neo4j-mcp

### 1-context
status: done

DOMAIN=social
USE_CASE=friend recommendations and community discovery
EXPERIENCE=beginner
DB_TARGET=aura-free
DATA_SOURCE=synthetic
APP_TYPE=notebook
LANGUAGE=python
EXEC_METHOD=cypher-shell

### 2-provision
status: done
NEO4J_URI=neo4j+s://c16f6104.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_DATABASE=neo4j
INSTANCE_ID=c16f6104
files=scripts/provision_aura.py

### 3-model
status: done
labels=Person,Post,Hashtag,Community
relationships=FOLLOWS,POSTED,TAGGED,MEMBER_OF,LIKED
constraints=4
files=schema/schema.json,schema/schema.cypher
sample_id=p1

### 6-query
status: done
queries_total=10
traversal_queries=6
queries_returning_rows=8
files=queries/queries.cypher

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40c16f6104.databases.neo4j.io
viz_method=browser

### 4-load
status: done
nodes=200 Person, 300 Post, 17 Hashtag, 10 Community
relationships=1765 FOLLOWS, 1202 LIKED, 605 TAGGED, 509 MEMBER_OF, 300 POSTED
files=data/generate.py,data/import.py,schema/reset.cypher
sample_id=p1
