# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done
PYTHON=python3.14
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
EXEC_METHOD=mcp

### 2-provision
status: done
NEO4J_URI=neo4j+s://236c524a.databases.neo4j.io
INSTANCE_ID=236c524a

### 3-model
status: done
labels=Person,Post,Hashtag,Community
relationships=FOLLOWS,POSTED,TAGGED,MEMBER_OF,LIKED
constraints=4

### 4-load
status: done
nodes=200 Person, 50 Post, 20 Hashtag, 8 Community
relationships=1879 FOLLOWS, 993 LIKED, 502 MEMBER_OF, 132 TAGGED, 50 POSTED

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40236c524a.databases.neo4j.io
viz_method=browser

### 6-query
status: done
queries_total=10
traversal_queries=6
queries_returning_rows=10
