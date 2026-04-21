# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

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
EXEC_METHOD=query-api

### 2-provision
status: done
NEO4J_URI=neo4j+s://f1cad593.databases.neo4j.io

### 3-model
status: done
labels=Person,Post,Hashtag,Community
relationships=FOLLOWS,POSTED,TAGGED,MEMBER_OF,LIKED
constraints=4

### 4-load
status: done
nodes=200 Person, 300 Post, 20 Hashtag, 10 Community
relationships=2310 FOLLOWS, 300 POSTED, 600 TAGGED, 499 MEMBER_OF, 1733 LIKED

### 5-explore
status: done
browser_url=https://browser.neo4j.io/?connectURL=neo4j%2Bs%3A%2F%2Fneo4j%40f1cad593.databases.neo4j.io
viz_method=browser

### 6-query
status: done
queries_total=10
traversal_queries=6
queries_returning_rows=5

### 7-build
status: done
artifact=notebook.ipynb
app_type=notebook
run_command=jupyter notebook notebook.ipynb
