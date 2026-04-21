# Neo4j Getting-Started — Progress
<!-- Resume: grep for "status: pending" to find the next stage -->

### 0-prerequisites
status: done

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
NEO4J_URI=__NEO4J_URI__

### 3-model
status: done
labels=Person,Post
relationships=FOLLOWS,POSTED
constraints=3

### 4-load
status: done
nodes=200 Person, 50 Post
relationships=1400 FOLLOWS, 300 POSTED

### 5-explore
status: pending

### 6-query
status: pending

### 7-build
status: pending
