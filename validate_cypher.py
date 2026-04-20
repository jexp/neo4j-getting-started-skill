"""
validate_cypher.py — Extract Cypher blocks from skill markdown files and validate
each statement against a local Neo4j database.

Strategy:
- READ queries (MATCH/RETURN/WITH): EXPLAIN (no side effects)
- DDL (CREATE CONSTRAINT/INDEX, DROP): execute directly, clean up after
- CALL {} IN TRANSACTIONS: execute directly (empty DB = safe), clean up after
- SHOW: execute directly (read-only admin)
- Templates/placeholders: skip

Ignores notifications for missing labels/properties/rels (empty DB expected).
Reports syntax errors and unexpected warnings.
"""

import logging
import re
import sys
from pathlib import Path
from neo4j import GraphDatabase
from neo4j.exceptions import CypherSyntaxError, ClientError

_SUPPRESS_IN_STDERR = {
    "UnknownPropertyKeyWarning",
    "UnknownRelationshipTypeWarning",
    "UnknownLabelWarning",
    "ParameterNotProvided",
}

class _FilteredStderr:
    """Drop stderr lines that contain any of the suppressed notification codes."""
    def __init__(self, wrapped):
        self._w = wrapped
        self._buf = ""

    def write(self, s):
        self._buf += s
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            if not any(code in line for code in _SUPPRESS_IN_STDERR):
                self._w.write(line + "\n")

    def flush(self):
        if self._buf and not any(code in self._buf for code in _SUPPRESS_IN_STDERR):
            self._w.write(self._buf)
        self._buf = ""
        self._w.flush()

    def __getattr__(self, name):
        return getattr(self._w, name)

import sys as _sys
_sys.stderr = _FilteredStderr(_sys.stderr)

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")
DATABASE = "jtbd"

REFS_DIR = Path(__file__).parent / "neo4j-getting-started-skill/references"

SKIP_PATTERNS = [
    r"<[A-Za-z_]+>",    # <label>, <name>, etc. — template placeholders
    r"\$\{",             # shell variable interpolation
    r"^f['\"]",          # Python f-string fragment
]

IGNORE_CODES = {
    "Neo.ClientNotification.Statement.UnknownLabelWarning",
    "Neo.ClientNotification.Statement.UnknownPropertyKeyWarning",
    "Neo.ClientNotification.Statement.UnknownRelationshipTypeWarning",
    "Neo.ClientNotification.Statement.NoApplicableIndex",
    "Neo.ClientNotification.Statement.CartesianProduct",
    "Neo.ClientNotification.Statement.RepeatedRelationshipReference",
    "Neo.ClientNotification.Procedure.ProcedureWarning",
    "Neo.ClientNotification.Statement.ParameterNotProvided",
    "Neo.ClientNotification.Statement.FeatureDeprecationWarning",
    "Neo.ClientNotification.Schema.IndexOrConstraintAlreadyExists",  # IF NOT EXISTS — benign
}

DDL_RE = re.compile(
    r"^\s*(CREATE\s+(CONSTRAINT|INDEX|VECTOR\s+INDEX|FULLTEXT\s+INDEX|TEXT\s+INDEX)"
    r"|DROP\s+(CONSTRAINT|INDEX)"
    r")",
    re.IGNORECASE,
)
CALL_IN_TX_RE = re.compile(r"IN\s+TRANSACTIONS\s+OF", re.IGNORECASE)
SHOW_RE = re.compile(r"^\s*SHOW\s+", re.IGNORECASE)


def extract_cypher_blocks(md_path: Path):
    text = md_path.read_text()
    results = []
    for m in re.finditer(r"```(?:cypher|Cypher)\n(.*?)```", text, re.DOTALL):
        line_no = text[: m.start()].count("\n") + 1
        results.append((line_no, m.group(1).strip()))
    return results


def strip_pragma(stmt: str) -> str:
    return re.sub(r"^\s*CYPHER\s+\d+\s*\n?", "", stmt, flags=re.IGNORECASE).strip()


def split_statements(block: str):
    stmts = []
    for raw in block.split(";"):
        lines = [l for l in raw.splitlines()
                 if not l.strip().startswith("//") and not l.strip().startswith("--")]
        stmt = "\n".join(lines).strip()
        if stmt:
            stmts.append(stmt)
    return stmts


def classify(stmt: str):
    """Return ('skip', reason) | ('direct', None) | ('explain', None)."""
    for pat in SKIP_PATTERNS:
        if re.search(pat, stmt, re.MULTILINE):
            return "skip", "template/placeholder"
    core = strip_pragma(stmt)
    if DDL_RE.match(core):
        return "direct", None
    if SHOW_RE.match(core):
        return "direct", None
    has_load_csv = bool(re.search(r"LOAD\s+CSV", stmt, re.IGNORECASE))
    has_file_url = bool(re.search(r"file:///", stmt))
    has_params   = bool(re.search(r"\$\w+", stmt))

    if CALL_IN_TX_RE.search(stmt):
        # Execute directly only if no $params and no file:/// (HTTPS URLs are fine)
        if has_params or has_file_url:
            return "explain", None
        return "direct", None
    if has_load_csv:
        # Execute HTTPS LOAD CSV directly; file:/// won't resolve so EXPLAIN those
        if has_file_url:
            return "explain", None
        return "direct", None
    return "explain", None


def get_notifications(summary):
    notifs = getattr(summary, "notifications", None) or []
    result = []
    for n in notifs:
        if isinstance(n, dict):
            result.append({"code": n.get("code", ""), "title": n.get("title", ""), "description": n.get("description", "")})
        else:
            result.append({"code": getattr(n, "code", ""), "title": getattr(n, "title", ""), "description": getattr(n, "description", "")})
    return result


def run_stmt(session, stmt: str, explain: bool):
    query = f"EXPLAIN {stmt}" if explain else stmt
    try:
        result = session.run(query)
        summary = result.consume()
        warnings = [
            f"  [{n['code']}] {n['title']}: {n['description']}"
            for n in get_notifications(summary)
            if n["code"] not in IGNORE_CODES
        ]
        return warnings
    except (CypherSyntaxError, ClientError) as e:
        return [f"  ERROR: {e.message}"]
    except Exception as e:
        return [f"  UNEXPECTED: {type(e).__name__}: {e}"]


def cleanup(session):
    """Remove all data and schema objects created during validation."""
    session.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS").consume()
    for row in session.run("SHOW CONSTRAINTS YIELD name RETURN name").data():
        session.run(f"DROP CONSTRAINT `{row['name']}` IF EXISTS").consume()
    for row in session.run("SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name").data():
        session.run(f"DROP INDEX `{row['name']}` IF EXISTS").consume()


def main():
    md_files = sorted(REFS_DIR.rglob("*.md"))
    driver = GraphDatabase.driver(URI, auth=AUTH)

    total = 0
    skipped = 0
    passed = 0
    failed = 0
    failures = []

    with driver.session(database=DATABASE) as session:
        # Clean slate + create placeholder index needed by SEARCH EXPLAIN in cypher-authoring.md
        cleanup(session)
        session.run(
            "CREATE VECTOR INDEX index_name IF NOT EXISTS FOR (n:Node) ON (n.embedding) "
            "OPTIONS { indexConfig: { `vector.dimensions`: 1536, `vector.similarity_function`: 'cosine' } }"
        ).consume()

        for md_file in md_files:
            rel = md_file.relative_to(REFS_DIR.parent.parent)
            blocks = extract_cypher_blocks(md_file)
            if not blocks:
                continue

            for line_no, block in blocks:
                for stmt in split_statements(block):
                    total += 1
                    mode, reason = classify(stmt)

                    if mode == "skip":
                        skipped += 1
                        print(f"  SKIP   {rel}:{line_no}  ({reason})")
                        continue

                    warnings = run_stmt(session, stmt, explain=(mode == "explain"))
                    label = f"{rel}:{line_no}"
                    tag = "DIRECT" if mode == "direct" else "EXPLAIN"
                    if warnings:
                        failed += 1
                        failures.append((label, stmt, warnings))
                        print(f"  FAIL   {label}  [{tag}]")
                        for w in warnings:
                            print(w)
                        print(f"         {stmt.splitlines()[0][:100]}")
                    else:
                        passed += 1
                        print(f"  OK     {label}  [{tag}]")

        cleanup(session)

    driver.close()

    print(f"Total: {total}  Passed: {passed}  Skipped: {skipped}  Failed: {failed}")

    if failures:
        print("\nFAILURES:")
        for label, stmt, warns in failures:
            print(f"\n  {label}")
            print(f"  {stmt[:200]}")
            for w in warns:
                print(w)
        sys.exit(1)
    else:
        print("All validated statements passed.")


if __name__ == "__main__":
    main()
