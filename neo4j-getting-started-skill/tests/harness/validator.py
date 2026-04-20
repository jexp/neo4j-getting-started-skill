"""
Getting-Started Skill Validator

Six-gate validation pipeline:
  Gate 1: db_running      — can connect to Neo4j
  Gate 2: model_valid     — schema has ≥N node labels + ≥M rel types
  Gate 3: data_present    — MATCH (n) RETURN count(n) > threshold
  Gate 4: queries_work    — queries.cypher has ≥5 queries, ≥3 return results
  Gate 5: app_generated   — expected app file exists and passes syntax check
  Gate 6: time_budget     — handled by runner.py
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from neo4j import GraphDatabase


class Validator:
    def __init__(self, work_dir: Path, persona: dict):
        self.work_dir = work_dir
        self.persona = persona
        self.expected = persona.get("expected_outputs", {})
        self.db_state = self.expected.get("db_state", {})
        self.query_config = self.expected.get("queries", {})
        self._driver = None

    def _get_driver(self):
        if self._driver:
            return self._driver
        env_path = self.work_dir / ".env"
        if not env_path.exists():
            raise FileNotFoundError(f".env not found in {self.work_dir}")

        env = {}
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

        uri = env.get("NEO4J_URI", "")
        user = env.get("NEO4J_USERNAME", "neo4j")
        password = env.get("NEO4J_PASSWORD", "")

        if not uri:
            # Fall back to test config demo DB
            tc = self.persona.get("test_config", {})
            demo = tc.get("demo_db", {})
            uri = demo.get("uri", "bolt://localhost:7687")
            user = demo.get("username", "neo4j")
            password = demo.get("password", "neo4j")

        # Retry driver creation up to 3 times with 10s delay — Aura DNS can be
        # transiently unresolvable immediately after a session ends.
        import time as _time
        last_exc = None
        for attempt in range(3):
            try:
                driver = GraphDatabase.driver(uri, auth=(user, password))
                driver.verify_connectivity()
                self._driver = driver
                return self._driver
            except Exception as e:
                last_exc = e
                if attempt < 2:
                    print(f"  [validator] connection attempt {attempt+1}/3 failed ({e}), retrying in 10s...")
                    _time.sleep(10)
        raise last_exc

    def _sample_id(self) -> str:
        """Read sample_id from progress.md or first CSV row, fallback to 'p1'."""
        progress = self.work_dir / "progress.md"
        if progress.exists():
            m = re.search(r"^sample_id=(.+)$", progress.read_text(), re.MULTILINE)
            if m:
                return m.group(1).strip().strip('"').strip("'")
        data_dir = self.work_dir / "data"
        if data_dir.exists():
            for csv_path in sorted(data_dir.glob("*.csv")):
                try:
                    import csv as _csv
                    with open(csv_path) as f:
                        row = next(_csv.DictReader(f), None)
                        if row:
                            for key in ("id", "ID", next(iter(row))):
                                if key in row:
                                    return row[key]
                except Exception:
                    pass
        return "p1"

    def check(self, gate_id: str) -> tuple[bool, str]:
        method = getattr(self, f"_gate_{gate_id}", None)
        if method is None:
            return False, f"Unknown gate: {gate_id}"
        return method()

    # ── Gate 1: DB running ─────────────────────────────────────────────────────

    def _gate_db_running(self) -> tuple[bool, str]:
        try:
            self._get_driver()  # already verifies connectivity + retries
            return True, "Connected successfully"
        except Exception as e:
            return False, f"Connection failed: {e}"

    # ── Gate 2: Model valid ────────────────────────────────────────────────────

    def _gate_model_valid(self) -> tuple[bool, str]:
        min_labels = self.db_state.get("min_node_labels", 2)
        min_rels = self.db_state.get("min_rel_types", 1)

        try:
            driver = self._get_driver()

            # Check constraints (present as soon as schema.cypher is applied, before any data)
            records, _, _ = driver.execute_query(
                "SHOW CONSTRAINTS YIELD labelsOrTypes, type "
                "RETURN collect(DISTINCT labelsOrTypes[0]) AS labels, count(*) AS constraintCount"
            )
            labels = records[0]["labels"] if records else []
            constraint_count = records[0]["constraintCount"] if records else 0

            # Also check relationship types from schema.json if constraints don't cover them
            schema_json = self.work_dir / "schema" / "schema.json"
            rel_types_from_schema = []
            if schema_json.exists():
                try:
                    schema = json.loads(schema_json.read_text())
                    rel_types_from_schema = [r["type"] for r in schema.get("relationships", [])]
                except Exception:
                    pass

            if len(labels) < min_labels and constraint_count == 0:
                # Fallback: check db.labels() in case data was loaded without constraints
                records2, _, _ = driver.execute_query(
                    "CALL db.labels() YIELD label RETURN collect(label) AS labels"
                )
                labels = records2[0]["labels"] if records2 else []

            if len(labels) < min_labels:
                return False, (
                    f"Only {len(labels)} constrained node labels (need ≥{min_labels}): {labels}. "
                    f"schema.cypher may not have been applied."
                )

            rel_count = len(rel_types_from_schema)
            if rel_count < min_rels:
                # Last resort: check live DB
                records3, _, _ = driver.execute_query(
                    "CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN collect(relationshipType) AS types"
                )
                live_rels = records3[0]["types"] if records3 else []
                rel_count = len(live_rels)

            if rel_count < min_rels:
                return False, f"Only {rel_count} relationship types in schema (need ≥{min_rels})"

            return True, f"{len(labels)} labels, {rel_count} rel types, {constraint_count} constraints"
        except Exception as e:
            return False, f"Schema check failed: {e}"

    # ── Gate 3: Data present ───────────────────────────────────────────────────

    def _gate_data_present(self) -> tuple[bool, str]:
        min_nodes = self.db_state.get("min_nodes", 10)

        try:
            driver = self._get_driver()
            records, _, _ = driver.execute_query(
                "MATCH (n) RETURN count(n) AS n"
            )
            count = records[0]["n"] if records else 0
            if count < min_nodes:
                return False, f"Only {count} nodes (need ≥{min_nodes})"
            return True, f"{count} nodes present"
        except Exception as e:
            return False, f"Data check failed: {e}"

    # ── Gate 4: Queries work ───────────────────────────────────────────────────

    def _gate_queries_work(self) -> tuple[bool, str]:
        min_queries = self.query_config.get("min_count", 5)
        min_returning = self.query_config.get("min_returning_results", 3)

        queries_file = self.work_dir / "queries" / "queries.cypher"
        if not queries_file.exists():
            # fallback: root-level queries.cypher from older runs
            queries_file = self.work_dir / "queries.cypher"
        if not queries_file.exists():
            return False, "queries/queries.cypher not found"

        cypher_text = queries_file.read_text()
        # Split on semicolons — each statement is one query
        # Strip comment-only segments and blank segments
        raw_segments = cypher_text.split(";")
        queries = []
        for seg in raw_segments:
            # Remove comment lines and blank lines, keep non-comment content
            content_lines = [
                ln for ln in seg.splitlines()
                if ln.strip() and not ln.strip().startswith("//")
            ]
            content = "\n".join(content_lines).strip()
            if content:
                queries.append(seg.strip())  # keep original for execution

        if len(queries) < min_queries:
            return False, f"Only {len(queries)} queries found (need ≥{min_queries})"

        # Execute each query and count results
        driver = self._get_driver()
        passing = 0
        errors = []
        for i, query in enumerate(queries[:10]):  # test up to 10
            try:
                # Extract inline comment defaults: // $paramName = "value" or // $paramName = 123
                comment_defaults = {}
                for m in re.finditer(r'//[^\n]*\$(\w+)\s*=\s*["\']?([^"\';\n,\s]+)["\']?', query):
                    comment_defaults[m.group(1)] = m.group(2).strip('"\'')

                sample_id = self._sample_id()
                test_query = query
                # Apply comment defaults first (most specific)
                for param, val in comment_defaults.items():
                    test_query = re.sub(rf'\${param}\b', f"'{val}'" if not val.isdigit() else val, test_query)
                # Fall back to sample_id for remaining id-like params
                test_query = re.sub(r'\$id\b', f"'{sample_id}'", test_query)
                test_query = re.sub(r'\$\w*[Ii]d\b', f"'{sample_id}'", test_query)
                test_query = re.sub(r'\$limit\b', "10", test_query)
                test_query = re.sub(r'\$threshold\b', "0", test_query)
                test_query = re.sub(r'\$\w+', "'test'", test_query)
                records, _, _ = driver.execute_query(test_query)
                if len(records) >= 1:
                    passing += 1
            except Exception as e:
                errors.append(f"Query {i+1}: {str(e)[:100]}")

        if passing < min_returning:
            msg = f"{passing}/{len(queries)} queries return results (need ≥{min_returning})"
            if errors:
                msg += f". Errors: {errors[:2]}"
            return False, msg

        return True, f"{passing}/{len(queries)} queries return results"

    # ── Gate 5: Graph visible ─────────────────────────────────────────────────

    def _gate_graph_visible(self) -> tuple[bool, str]:
        progress = self.work_dir / "progress.md"
        if progress.exists():
            text = progress.read_text()
            # Look for browser_url= in the 5-explore section
            import re
            m = re.search(r"### 5-explore.*?browser_url=(\S+)", text, re.DOTALL)
            if m:
                return True, f"Browser URL recorded: {m.group(1)[:60]}"
        # Fallback: scan stdout for browser URL pattern
        return False, "No browser_url found in progress.md (5-explore section)"

    # ── Gate 6: App generated ──────────────────────────────────────────────────

    def _gate_app_generated(self) -> tuple[bool, str]:
        app_type = self.persona["inputs"]["app_type"]
        language = self.persona["inputs"].get("language", "python")

        # Expected files by app type — check both root and app/ subfolder
        candidates = {
            "notebook": ["notebook.ipynb"],
            "streamlit": ["app.py"],
            "fastapi": ["main.py"],
            "express": ["server.js"],
            "queries-only": ["queries/queries.cypher", "queries.cypher", "README.md"],
            "mcp": [".claude/settings.json", "mcp_config.json"],
        }

        expected_files = candidates.get(app_type, ["app.py"])
        found = [f for f in expected_files if (self.work_dir / f).exists()]

        if not found:
            return False, f"None of {expected_files} found in work dir"

        # Syntax check
        primary = self.work_dir / found[0]
        if primary.suffix == ".py":
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(primary)],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                return False, f"Syntax error in {found[0]}: {result.stderr[:200]}"
        elif primary.suffix == ".ipynb":
            try:
                json.loads(primary.read_text())
            except json.JSONDecodeError as e:
                return False, f"Invalid notebook JSON: {e}"
        elif primary.suffix == ".js":
            # Basic check: file is non-empty and has require/import
            content = primary.read_text()
            if len(content) < 50:
                return False, f"{found[0]} is too short ({len(content)} chars)"

        return True, f"{found[0]} generated and valid"

    # ── Gate 6: MCP configured ─────────────────────────────────────────────────

    def _gate_mcp_configured(self) -> tuple[bool, str]:
        candidates = [
            self.work_dir / ".claude" / "settings.json",
            Path.home() / ".claude" / "settings.json",
            self.work_dir / "mcp_config.json",
        ]
        # Also accept any mcp-*.json file in the work dir root
        candidates += list(self.work_dir.glob("mcp-*.json"))

        for path in candidates:
            if path.exists():
                try:
                    config = json.loads(path.read_text())
                    # Standard mcpServers format
                    servers = config.get("mcpServers", {})
                    neo4j_keys = [k for k in servers if "neo4j" in k.lower()]
                    if neo4j_keys:
                        return True, f"MCP config found at {path.name} with servers: {neo4j_keys}"
                    # Flat format: {"command": ..., "args": [...]} containing neo4j
                    content = path.read_text().lower()
                    if "neo4j" in content and ("command" in content or "args" in content):
                        return True, f"MCP config found at {path.name} (neo4j reference present)"
                except Exception:
                    pass
        return False, "No MCP config with neo4j server found"

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
