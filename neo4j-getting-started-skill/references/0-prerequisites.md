# Stage 0 — prerequisites
# Verify and install required CLI tools before anything else.

## neo4j-mcp (official Neo4j MCP server — required)

MCP tool names exposed by this server:
- `get-schema` — introspect node labels, relationship types, property keys
- `read-cypher` — execute read-only Cypher
- `write-cypher` — execute write Cypher (disabled in read-only mode)
- `list-gds-procedures` — list available GDS procedures (only if GDS is installed)

```bash
# Check if already installed
which neo4j-mcp 2>/dev/null || ls $HOME/bin/neo4j-mcp 2>/dev/null && echo "FOUND" || echo "MISSING"
```

If missing, download binary:
```bash
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
[ "$ARCH" = "x86_64" ] && ARCH="amd64"
[ "$ARCH" = "aarch64" ] && ARCH="arm64"
curl -fsSL "https://github.com/neo4j/mcp/releases/latest/download/neo4j-mcp-${PLATFORM}-${ARCH}" \
  -o ./neo4j-mcp && chmod +x ./neo4j-mcp
./neo4j-mcp --version
```

The binary can live in `./neo4j-mcp` (project-local) or `$HOME/bin/neo4j-mcp` (user-wide). Either works.

## aura-cli (optional — for Aura provisioning via CLI)

```bash
which aura-cli 2>/dev/null && echo "FOUND" || echo "MISSING — using Aura REST API directly (no install needed)"
```

aura-cli is **not required** — the `provision` stage uses the Aura REST API via `curl` as the primary path, which works without any binary.

## Docker (optional — for local Docker path only)

```bash
docker --version 2>/dev/null && echo "FOUND" || echo "MISSING"
```

## Python (required for app generation)

```bash
python3 --version   # need >=3.10
```

## .gitignore setup (always run)

```bash
for entry in .env aura.env neo4j-mcp; do
  grep -qxF "$entry" .gitignore 2>/dev/null || echo "$entry" >> .gitignore
done
echo "✓ .gitignore updated"
```

## Completion condition

- `neo4j-mcp` binary reachable (local or on PATH)
- `.gitignore` contains `.env` and `aura.env`
- Python ≥3.10 available

## On Completion — write to progress.md

```markdown
### 0-prerequisites
status: done
```
