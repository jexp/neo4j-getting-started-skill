# Stage 2 — provision
# Provision a running Neo4j database and save credentials to .env.

## Aura REST API

Use these three endpoints directly — no extra tooling needed. For all other operations
(list, delete, pause, resume, update), fetch the live OpenAPI spec at runtime:
`GET https://api.neo4j.io/openapi.json` or browse `https://neo4j.com/docs/aura/platform/api/specification/`

### Step P-1 — Collect Aura API credentials

`aura.env` holds account-level API credentials (reusable across instances).
`.env` holds per-instance DB connection details (written later in P3).
They must be kept separate so writing `.env` never overwrites the API key.

Check in order:
1. `aura.env` exists → load it with Python (see Step P0) → proceed
2. Environment variables `CLIENT_ID` / `CLIENT_SECRET` (or `AURA_CLIENT_ID` / `AURA_CLIENT_SECRET`) already set → proceed
3. Neither found → **ask the user**:

> "To provision an Aura database I need your Aura API credentials.
> Please go to https://console.neo4j.io → Account Settings → API credentials,
> create a new client, and paste the **Client ID** and **Client Secret** here."

Once received, save to `aura.env` (never `.env`):
```bash
cat > aura.env << EOF
CLIENT_ID=<value>
CLIENT_SECRET=<value>
# Strongly recommended for users with multiple organisations or projects —
# without these the API picks the first org/project alphabetically which may be wrong.
# Find them at console.neo4j.io → your project → Settings.
# PROJECT_ID=<project/tenant id>
# ORGANIZATION_ID=<organisation id>
EOF
# aura.env is already in .gitignore from the prerequisites stage
```

The console generates keys named `CLIENT_ID` / `CLIENT_SECRET`. Both that form and `AURA_CLIENT_ID` / `AURA_CLIENT_SECRET` are accepted.

### Steps P0–P3 — Provision via Python script

**Run the entire provision flow as a single Python script.** Environment variables set in
one Bash tool call are lost in the next call, so do not split this across multiple commands.

```python
#!/usr/bin/env python3
"""
provision_aura.py — run this script to provision an Aura Free instance.
Reads aura.env, creates the instance, polls until running, writes .env.
"""
import json, pathlib, time, urllib.request, urllib.error
from dotenv import dotenv_values

# ── Load aura.env ────────────────────────────────────────────────────────────
env = dotenv_values("aura.env")

CLIENT_ID     = env.get("CLIENT_ID") or env.get("AURA_CLIENT_ID")
CLIENT_SECRET = env.get("CLIENT_SECRET") or env.get("AURA_CLIENT_SECRET")
PROJECT_ID    = env.get("PROJECT_ID")      # optional — skip discovery if set
ORG_ID        = env.get("ORGANIZATION_ID") # optional — skip discovery if set

assert CLIENT_ID and CLIENT_SECRET, "CLIENT_ID / CLIENT_SECRET missing from aura.env"

def api(method, path, token=None, body=None, base="https://api.neo4j.io"):
    url = base + path
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} → {e.code}: {e.read().decode()}") from e

# ── Token ────────────────────────────────────────────────────────────────────
# Endpoint: /oauth/token  •  JSON body  •  NOT /oauth2/token  •  NOT form-encoded
token = api("POST", "/oauth/token", body={
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
})["access_token"]
print(f"✓ Token obtained ({token[:16]}...)")

# ── Resolve org + project (v2beta1 for correct scoping) ──────────────────────
if not ORG_ID:
    orgs = api("GET", "/v2beta1/organizations", token)["data"]
    ORG_ID = orgs[0]["id"]
    print(f"  Discovered ORGANIZATION_ID={ORG_ID}  ({orgs[0]['name']})")
else:
    print(f"  Using ORGANIZATION_ID={ORG_ID} from aura.env")

if not PROJECT_ID:
    projects = api("GET", f"/v2beta1/organizations/{ORG_ID}/projects", token)["data"]
    PROJECT_ID = projects[0]["id"]
    print(f"  Discovered PROJECT_ID={PROJECT_ID}  ({projects[0]['name']})")
else:
    print(f"  Using PROJECT_ID={PROJECT_ID} from aura.env")

# ── Create instance (v1beta5) ─────────────────────────────────────────────────
# If free quota is exceeded this raises RuntimeError — handled below.
try:
    result = api("POST", "/v1beta5/instances", token, body={
        "name": "myapp-db",
        "tenant_id": PROJECT_ID,
        "cloud_provider": "gcp",
        "region": "europe-west1",
        "type": "free-db",
        "memory": "1GB",
    })["data"]
    INSTANCE_ID = result["id"]
    PASSWORD     = result["password"]   # shown only once — captured here
    print(f"✓ Instance created: {INSTANCE_ID}")
except RuntimeError as e:
    if "quota" not in str(e).lower() and "limit" not in str(e).lower():
        raise
    # Free quota exceeded — fall back to a Pro trial instance (also free for new accounts)
    print(f"  Free quota exceeded. Falling back to professional-db trial instance...")
    result = api("POST", "/v1beta5/instances", token, body={
        "name": "myapp-db",
        "tenant_id": PROJECT_ID,
        "cloud_provider": "gcp",
        "region": "europe-west1",
        "type": "professional-db",
        "memory": "1GB",
    })["data"]
    INSTANCE_ID = result["id"]
    PASSWORD     = result["password"]
    print(f"✓ Pro trial instance created: {INSTANCE_ID}")

# ── Poll until running ────────────────────────────────────────────────────────
CONNECTION = ""
for i in range(1, 25):
    status_data = api("GET", f"/v1beta5/instances/{INSTANCE_ID}", token)["data"]
    status = status_data.get("status", "")
    CONNECTION = status_data.get("connection_url", "")
    print(f"  [{i}/24] {status}")
    if status == "running":
        break
    time.sleep(15)
else:
    raise RuntimeError("Instance did not reach 'running' after 6 minutes")

# ── Write .env ────────────────────────────────────────────────────────────────
pathlib.Path(".env").write_text(
    f"NEO4J_URI={CONNECTION}\n"
    f"NEO4J_USERNAME=neo4j\n"
    f"NEO4J_PASSWORD={PASSWORD}\n"
    f"NEO4J_DATABASE=neo4j\n"
)
print(f"✓ .env written  URI={CONNECTION}")
```

Write this to `provision_aura.py` and run it:
```bash
python3 provision_aura.py
```

---

## Aura CLI Quick Reference

### Installation
```bash
# macOS
brew install neo4j/tap/aura-cli   # if homebrew tap exists
# or: download binary from https://github.com/neo4j/aura-cli/releases/latest
sudo mv aura-cli /usr/local/bin/ && chmod +x /usr/local/bin/aura-cli

# Verify
aura-cli --version
```

### Credential setup
```bash
# Generate Client ID + Secret at https://console.neo4j.io → Account Settings → API credentials
aura-cli credential add \
  --name "default" \
  --client-id $AURA_CLIENT_ID \
  --client-secret $AURA_CLIENT_SECRET
```

### Instance lifecycle
```bash
# Create Free instance (512MB, GCP)
aura-cli instance create \
  --name "myapp-db" \
  --cloud-provider gcp \
  --region europe-west1 \
  --type free-db \
  --output json

# Create Pro instance (1GB, AWS)
aura-cli instance create \
  --name "myapp-prod" \
  --cloud-provider aws \
  --region us-east-1 \
  --type professional-db \
  --memory 1 \
  --output json

# List instances
aura-cli instance list --output json

# Get single instance status (check for "running")
aura-cli instance get <INSTANCE_ID> --output json

# Pause / resume (cost saving)
aura-cli instance pause <INSTANCE_ID>
aura-cli instance resume <INSTANCE_ID>

# Delete
aura-cli instance delete <INSTANCE_ID>
```

### Regions by cloud provider
| Provider | Available Regions |
|----------|------------------|
| GCP | us-central1, us-east1, europe-west1, europe-west3, asia-east1, asia-southeast1 |
| AWS | us-east-1, us-west-2, eu-west-1, eu-central-1, ap-southeast-1 |
| Azure | eastus, westeurope, southeastasia |

### Poll for running status (bash)
```bash
INSTANCE_ID="<id>"
for i in $(seq 1 24); do
  STATUS=$(aura-cli instance get $INSTANCE_ID --output json | \
           python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','unknown'))")
  echo "[$i/24] Status: $STATUS"
  [ "$STATUS" = "running" ] && { echo "Instance ready"; break; }
  sleep 15
done
```

---

## Docker Quick Reference

```bash
# Basic (ephemeral)
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  neo4j:latest

# With plugins (APOC + GDS)
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -e NEO4J_PLUGINS='["apoc","graph-data-science"]' \
  neo4j:latest

# Persistent data volume
docker run -d \
  --name neo4j-dev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -v $HOME/neo4j/data:/data \
  neo4j:latest

# Check logs
docker logs neo4j-dev -f

# Stop / remove
docker stop neo4j-dev && docker rm neo4j-dev
```

---

## Connectivity Verification

### cypher-shell
```bash
cypher-shell -a "neo4j+s://xxxxx.databases.neo4j.io" \
             -u neo4j -p "<password>" \
             "RETURN 'connected' AS status"
```

### Python
```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    "neo4j+s://xxxxx.databases.neo4j.io",
    auth=("neo4j", "<password>")
)
driver.verify_connectivity()
print("Connected")
driver.close()
```

### Node.js
```javascript
const neo4j = require('neo4j-driver');
const driver = neo4j.driver(
  'neo4j+s://xxxxx.databases.neo4j.io',
  neo4j.auth.basic('neo4j', '<password>')
);
await driver.verifyConnectivity();
console.log('Connected');
await driver.close();
```

---

## Neo4j Query API (HTTP — no driver required)

Useful for connectivity checks and scripting when no driver is installed:

```bash
# Aura: host is the bolt URI without the scheme
HOST="xxxxx.databases.neo4j.io"
curl -s -X POST "https://${HOST}/db/neo4j/query/v2" \
  -H "Content-Type: application/json" \
  -u "neo4j:<password>" \
  -d '{"statement": "MATCH (n) RETURN count(n) AS total"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d)"

# Local Docker
curl -s -X POST "http://localhost:7474/db/neo4j/query/v2" \
  -H "Content-Type: application/json" \
  -u "neo4j:password123" \
  -d '{"statement": "RETURN 1"}'
```

---

## URI Schemes

| Scheme | Use case |
|--------|----------|
| `neo4j+s://` | Aura (TLS required) |
| `bolt+s://` | Self-hosted with TLS |
| `bolt://` | Local development (no TLS) |
| `neo4j://` | Cluster routing, no TLS |

---

## On Completion — write to progress.md

```markdown
### 2-provision
status: done
NEO4J_URI=<value from .env>
```

## .env File Template
```
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<generated-password>
NEO4J_DATABASE=neo4j
```
