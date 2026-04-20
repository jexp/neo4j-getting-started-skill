"""
Getting-Started Skill Test Runner

Installs the skill to ~/.claude/skills/, invokes Claude Code using the
/neo4j-getting-started-skill slash command, validates success gates, then
uninstalls the skill.

Usage:
    python3 tests/harness/runner.py --persona tests/personas/alex_beginner.yml
    python3 tests/harness/runner.py --persona tests/personas/sam_developer.yml --verbose
    python3 tests/harness/runner.py --all-personas
    python3 tests/harness/runner.py --persona tests/personas/alex_beginner.yml --keep-skill
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tempfile
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

SKILL_NAME = "neo4j-getting-started-skill"
SKILL_SRC = Path(__file__).parent.parent.parent          # the neo4j-getting-started-skill/ folder
SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills" / SKILL_NAME
RESULTS_DIR = Path(__file__).parent.parent / "results"

# aura.env lives one level above the skill folder (repo root).
# Copy it into each temp work dir so the skill can find Aura API credentials.
AURA_ENV_SRC = SKILL_SRC.parent / "aura.env"


@dataclass
class GateResult:
    gate_id: str
    passed: bool
    message: str
    elapsed_ms: int = 0


@dataclass
class RunResult:
    persona_id: str
    started_at: str
    ended_at: str
    total_seconds: float
    gates: List[GateResult] = field(default_factory=list)
    work_dir: str = ""
    stdout: str = ""
    stderr: str = ""

    @property
    def passed(self) -> bool:
        return all(g.passed for g in self.gates)

    @property
    def gate_summary(self) -> str:
        passed = sum(1 for g in self.gates if g.passed)
        return f"{passed}/{len(self.gates)} gates passed"


def install_skill(verbose: bool = False) -> None:
    """Install skill source to ~/.claude/skills/."""
    if SKILL_INSTALL_DIR.exists():
        shutil.rmtree(SKILL_INSTALL_DIR)
    shutil.copytree(str(SKILL_SRC), str(SKILL_INSTALL_DIR))
    if verbose:
        print(f"[Runner] Skill installed: {SKILL_INSTALL_DIR}")


def uninstall_skill(verbose: bool = False) -> None:
    """Remove skill from ~/.claude/skills/."""
    if SKILL_INSTALL_DIR.exists():
        shutil.rmtree(SKILL_INSTALL_DIR)
        if verbose:
            print(f"[Runner] Skill uninstalled: {SKILL_INSTALL_DIR}")


def _load_env(env_path: Path) -> dict:
    from dotenv import dotenv_values
    return dotenv_values(env_path)


def wipe_database(env_path: Path, verbose: bool = False) -> None:
    """Delete all nodes, relationships, constraints, and indexes — fresh slate."""
    from neo4j import GraphDatabase
    env = _load_env(env_path)
    uri      = env.get("NEO4J_URI", "")
    user     = env.get("NEO4J_USERNAME", "neo4j")
    password = env.get("NEO4J_PASSWORD", "")
    database = env.get("NEO4J_DATABASE", "neo4j")
    if not uri or not password:
        print("[Runner] WARNING: .env incomplete — skipping wipe")
        return
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=database) as s:
            s.run("MATCH (n) CALL (n) { DETACH DELETE n } IN TRANSACTIONS OF 1000 ROWS")
            constraints = [r["name"] for r in s.run("SHOW CONSTRAINTS YIELD name RETURN name")]
            for name in constraints:
                s.run(f"DROP CONSTRAINT `{name}`")
            indexes = [r["name"] for r in s.run(
                "SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name"
            )]
            for name in indexes:
                s.run(f"DROP INDEX `{name}`")
        driver.close()
        if verbose:
            print(f"[Runner] DB wiped ({len(constraints)} constraints, {len(indexes)} indexes dropped)")
    except Exception as e:
        print(f"[Runner] WARNING: DB wipe failed: {e}")


def capture_db_snapshot(work_dir: Path, results_stem: str, verbose: bool = False) -> Optional[Path]:
    """Export node/rel counts and sample data to results/<stem>_db_snapshot.json."""
    env_path = work_dir / ".env"
    if not env_path.exists():
        return None
    try:
        from neo4j import GraphDatabase
        env      = _load_env(env_path)
        uri      = env.get("NEO4J_URI", "")
        user     = env.get("NEO4J_USERNAME", "neo4j")
        password = env.get("NEO4J_PASSWORD", "")
        database = env.get("NEO4J_DATABASE", "neo4j")
        if not uri or not password:
            return None

        driver = GraphDatabase.driver(uri, auth=(user, password))
        snap = {}

        recs, _, _ = driver.execute_query(
            "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count ORDER BY count DESC",
            database_=database
        )
        snap["node_counts"] = [dict(r) for r in recs]

        recs, _, _ = driver.execute_query(
            "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count ORDER BY count DESC",
            database_=database
        )
        snap["rel_counts"] = [dict(r) for r in recs]

        recs, _, _ = driver.execute_query(
            "SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties RETURN *",
            database_=database
        )
        snap["constraints"] = [dict(r) for r in recs]

        # Sample nodes per label (up to 10)
        label_recs, _, _ = driver.execute_query(
            "CALL db.labels() YIELD label RETURN label", database_=database
        )
        snap["sample_nodes"] = {}
        for lr in label_recs:
            label = lr["label"]
            srecs, _, _ = driver.execute_query(
                f"MATCH (n:`{label}`) RETURN properties(n) AS props LIMIT 10",
                database_=database
            )
            snap["sample_nodes"][label] = [r["props"] for r in srecs]

        driver.close()

        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out = RESULTS_DIR / f"{results_stem}_db_snapshot.json"
        out.write_text(json.dumps(snap, indent=2, default=str))
        total_nodes = sum(r.get("count", 0) for r in snap["node_counts"])
        total_rels  = sum(r.get("count", 0) for r in snap["rel_counts"])
        if verbose:
            print(f"[Runner] DB snapshot: {total_nodes} nodes, {total_rels} rels → {out.name}")
        return out
    except Exception as e:
        print(f"[Runner] WARNING: DB snapshot failed: {e}")
        return None


def delete_aura_instance(instance_id: str, verbose: bool = False) -> bool:
    """Delete a provisioned Aura instance via REST API. Returns True on success."""
    if not AURA_ENV_SRC.exists():
        print("[Runner] WARNING: aura.env not found — cannot delete instance")
        return False
    env = _load_env(AURA_ENV_SRC)
    client_id     = env.get("CLIENT_ID") or env.get("AURA_CLIENT_ID")
    client_secret = env.get("CLIENT_SECRET") or env.get("AURA_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("[Runner] WARNING: CLIENT_ID/CLIENT_SECRET missing — cannot delete instance")
        return False

    def _api(method, path, token=None, body=None):
        url  = "https://api.neo4j.io" + path
        data = json.dumps(body).encode() if body else None
        hdrs = {"Content-Type": "application/json"}
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        resp = urllib.request.urlopen(req)
        raw  = resp.read()
        return json.loads(raw) if raw else {}

    try:
        token = _api("POST", "/oauth/token", body={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        })["access_token"]
        _api("DELETE", f"/v1beta5/instances/{instance_id}", token)
        if verbose:
            print(f"[Runner] Aura instance {instance_id} deleted")
        return True
    except Exception as e:
        print(f"[Runner] WARNING: failed to delete instance {instance_id}: {e}")
        return False


def _read_instance_id(work_dir: Path) -> Optional[str]:
    """Extract INSTANCE_ID from progress.md written by the provision stage."""
    progress = work_dir / "progress.md"
    if not progress.exists():
        return None
    m = re.search(r"^INSTANCE_ID=(.+)$", progress.read_text(), re.MULTILINE)
    return m.group(1).strip() if m else None


def load_persona(persona_path: str) -> dict:
    with open(persona_path) as f:
        return yaml.safe_load(f)


def build_initial_prompt(persona: dict) -> str:
    """Build the initial user message from persona inputs."""
    inputs = persona["inputs"]
    p = persona["persona"]

    return (
        f"I want to get started with Neo4j. "
        f"Domain: {inputs['domain']}, "
        f"use-case: {inputs['use_case']}, "
        f"experience: {inputs['experience']} ({p['background']}), "
        f"database: {inputs['db_target']}, "
        f"data: {inputs['data_source']}, "
        f"app: {inputs['app_type']} in {inputs.get('language', 'python')}, "
        f"integration: {inputs.get('integration', 'none')}. "
        f"Please guide me through the complete getting-started process."
    )


def run_skill(persona: dict, work_dir: Path, verbose: bool = False) -> tuple[str, str, float]:
    """
    Invoke Claude Code from a clean temp work directory with the skill injected
    via --append-system-prompt. All generated files land in work_dir.
    Returns (stdout, stderr, elapsed_seconds).
    """
    skill_md = (SKILL_SRC / "SKILL.md").read_text()
    prompt = build_initial_prompt(persona)

    max_turns = persona.get("test_config", {}).get("max_turns", 55)

    cmd = [
        "claude",
        "--print",                          # non-interactive
        "--dangerously-skip-permissions",   # no approval prompts
        "--output-format", "stream-json",   # stream events as they arrive
        "--verbose",                        # required for stream-json
        "--max-turns", str(max_turns),      # prevent runaway sessions
        "--append-system-prompt", skill_md,
        "-p", prompt,
    ]

    if verbose:
        print(f"\n[Runner] Work dir (temp): {work_dir}")
        print(f"[Runner] Prompt: {prompt[:120]}...")

    import io, threading

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    def stream_stdout(src, buf):
        run_start   = time.time()
        last_time   = run_start
        total_in    = 0
        total_out   = 0
        stage_times: list = []   # [(stage_name, elapsed_s)]
        current_stage = "start"

        for raw in src:
            buf.write(raw)
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue

            now = time.time()
            t = ev.get("type", "")

            if t == "assistant":
                msg     = ev.get("message", {})
                usage   = msg.get("usage", {})
                in_tok  = usage.get("input_tokens", 0)
                out_tok = usage.get("output_tokens", 0)
                total_in  += in_tok
                total_out += out_tok
                dt = now - last_time
                last_time = now

                for block in msg.get("content", []):
                    bt = block.get("type")
                    if bt == "text":
                        text = block["text"]
                        # detect stage transitions and annotate
                        for line in text.splitlines():
                            if line.startswith("## Stage:"):
                                stage_name = line.replace("## Stage:", "").split("—")[0].strip()
                                elapsed = now - run_start
                                stage_times.append((current_stage, elapsed))
                                current_stage = stage_name
                                sys.stdout.write(f"\n[+{elapsed:.0f}s] ")
                        sys.stdout.write(text)
                        sys.stdout.flush()
                    elif bt == "tool_use":
                        name = block.get("name", "?")
                        inp  = str(block.get("input", ""))[:100]
                        tok_str = f" {in_tok}→{out_tok}tok" if (in_tok or out_tok) else ""
                        sys.stdout.write(f"\n  [tool +{dt:.1f}s{tok_str}] {name}  {inp}\n")
                        sys.stdout.flush()
                        dt = 0  # reset after first tool in this message

            elif t == "result":
                cost   = ev.get("total_cost_usd")
                turns  = ev.get("num_turns")
                total_elapsed = now - run_start
                cost_str = f"  cost=${cost:.4f}" if cost else ""
                tok_str  = f"  tokens={total_in}in/{total_out}out" if total_in else ""
                sys.stdout.write(
                    f"\n[Runner] done — turns={turns}  elapsed={total_elapsed:.0f}s"
                    f"{cost_str}{tok_str}\n"
                )
                # Stage timing summary — merge announced stages with known order
                if stage_times:
                    KNOWN = ["0-prerequisites","1-context","2-provision","3-model",
                             "4-load","5-explore","6-query","7-build"]
                    announced = {s for s, _ in stage_times}
                    # insert skipped stages at 0s so timing rows are complete
                    full = []
                    for s, t in stage_times:
                        full.append((s, t))
                        # if next known stage was skipped, add it at same timestamp
                        idx = KNOWN.index(s) if s in KNOWN else -1
                        if idx >= 0:
                            nxt = idx + 1
                            while nxt < len(KNOWN) and KNOWN[nxt] not in announced:
                                full.append((KNOWN[nxt], t))
                                nxt += 1
                    sys.stdout.write("[Runner] Stage timings:\n")
                    checkpoints = full + [(current_stage, total_elapsed)]
                    for i in range(len(checkpoints) - 1):
                        sname, t0 = checkpoints[i]
                        _, t1     = checkpoints[i + 1]
                        dt_s = t1 - t0
                        skipped = "(skipped)" if dt_s == 0 else f"{dt_s:.0f}s"
                        sys.stdout.write(f"  {sname:<22} {skipped}\n")
                sys.stdout.flush()
                break  # result is always the final stream-json event

    def stream_stderr(src, buf):
        for line in src:
            buf.write(line)
            sys.stderr.write(line)
            sys.stderr.flush()

    start = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=work_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    t_out = threading.Thread(target=stream_stdout, args=(proc.stdout, stdout_buf))
    t_err = threading.Thread(target=stream_stderr, args=(proc.stderr, stderr_buf))
    t_out.start(); t_err.start()

    timeout = persona["test_config"]["timeout_seconds"]
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
    finally:
        # Close pipes so streaming threads unblock if process left children holding them open
        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            proc.stderr.close()
        except Exception:
            pass
        t_out.join(timeout=5)
        t_err.join(timeout=5)

    elapsed = time.time() - start

    if verbose:
        print(f"[Runner] Elapsed: {elapsed:.1f}s  returncode: {proc.returncode}")

    return stdout_buf.getvalue(), stderr_buf.getvalue(), elapsed


def validate_gates(persona: dict, work_dir: Path, elapsed: float) -> List[GateResult]:
    """Run all success gate checks against the work directory."""
    from validator import Validator

    v = Validator(work_dir, persona)
    results = []

    for gate in persona["success_gates"]:
        t0 = time.time()
        try:
            passed, message = v.check(gate["id"])
        except Exception as e:
            passed, message = False, f"Exception: {e}"
        elapsed_ms = int((time.time() - t0) * 1000)
        results.append(GateResult(gate["id"], passed, message, elapsed_ms))

    # Time budget gate (special — uses overall elapsed)
    time_limit = persona["test_config"]["timeout_seconds"]
    passed = elapsed <= time_limit
    results.append(GateResult(
        "time_budget",
        passed,
        f"{elapsed:.1f}s / {time_limit}s limit",
        0
    ))

    return results


def save_results(run: RunResult) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{run.persona_id}_{ts}"
    out_path = RESULTS_DIR / f"{stem}.json"

    progress_md = Path(run.work_dir) / "progress.md"
    progress_content = progress_md.read_text() if progress_md.exists() else None

    with open(out_path, "w") as f:
        json.dump({
            "persona_id": run.persona_id,
            "started_at": run.started_at,
            "ended_at": run.ended_at,
            "total_seconds": run.total_seconds,
            "passed": run.passed,
            "gate_summary": run.gate_summary,
            "gates": [
                {"id": g.gate_id, "passed": g.passed, "message": g.message, "elapsed_ms": g.elapsed_ms}
                for g in run.gates
            ],
            "work_dir": run.work_dir,
            "progress_md": progress_content,
        }, f, indent=2)

    if progress_content:
        (RESULTS_DIR / f"{stem}_progress.md").write_text(progress_content)

    return out_path


def print_report(run: RunResult):
    status = "PASS" if run.passed else "FAIL"
    print(f"\n{'='*60}")
    print(f"Persona: {run.persona_id}  [{status}]")
    print(f"Total time: {run.total_seconds:.1f}s")
    print(f"Gates: {run.gate_summary}")
    print(f"{'-'*60}")
    for g in run.gates:
        icon = "✓" if g.passed else "✗"
        print(f"  {icon} {g.gate_id:<20} {g.message}")
    print(f"{'='*60}\n")


def run_persona(persona_path: str, verbose: bool = False, keep_skill: bool = False,
                fixture_dir: Optional[str] = None, delete_db: bool = False) -> RunResult:
    persona = load_persona(persona_path)
    persona_id = persona["persona"]["id"]

    # Fresh temp dir — Claude runs here; all generated files stay isolated
    work_dir = Path(tempfile.mkdtemp(prefix=f"neo4j_skill_{persona_id}_"))
    started_at = datetime.now().isoformat()

    print(f"\n[Runner] Starting persona: {persona_id}")
    print(f"[Runner] Work dir: {work_dir}")

    # Copy fixture files first (progress.md, schema/, etc.) if provided
    if fixture_dir:
        fixture_path = Path(fixture_dir)
        for item in fixture_path.iterdir():
            dest = work_dir / item.name
            if item.is_file():
                shutil.copy(str(item), str(dest))
            elif item.is_dir():
                shutil.copytree(str(item), str(dest))
        if verbose:
            print(f"[Runner] Copied fixture files from {fixture_path}")

    if AURA_ENV_SRC.exists():
        shutil.copy(str(AURA_ENV_SRC), str(work_dir / "aura.env"))
        if verbose:
            print(f"[Runner] Copied aura.env → {work_dir}/aura.env")

        # If aura.env contains NEO4J_URI + NEO4J_PASSWORD, write .env so the
        # skill skips provisioning and goes straight to model/load.
        from dotenv import dotenv_values
        aura_vars = dotenv_values(AURA_ENV_SRC)
        if aura_vars.get("NEO4J_URI") and aura_vars.get("NEO4J_PASSWORD"):
            dot_env_path = work_dir / ".env"
            dot_env_path.write_text(
                f"NEO4J_URI={aura_vars['NEO4J_URI']}\n"
                f"NEO4J_USERNAME={aura_vars.get('NEO4J_USERNAME', 'neo4j')}\n"
                f"NEO4J_PASSWORD={aura_vars['NEO4J_PASSWORD']}\n"
                f"NEO4J_DATABASE={aura_vars.get('NEO4J_DATABASE', 'neo4j')}\n"
            )
            print(f"[Runner] Pre-populated .env from aura.env (skips provisioning)")
            # Wipe the pre-existing DB so each run starts from a clean slate
            print("[Runner] Wiping pre-existing database for clean test run...")
            wipe_database(dot_env_path, verbose=verbose)
            # Patch __NEO4J_URI__ placeholder in fixture progress.md if present
            progress_md = work_dir / "progress.md"
            if progress_md.exists():
                content = progress_md.read_text()
                if "__NEO4J_URI__" in content:
                    progress_md.write_text(content.replace("__NEO4J_URI__", aura_vars["NEO4J_URI"]))
                    if verbose:
                        print(f"[Runner] Patched NEO4J_URI in fixture progress.md")
    else:
        print(f"[Runner] WARNING: {AURA_ENV_SRC} not found — skill will prompt for Aura credentials")

    # Track whether .env was pre-populated (pre-existing DB) or will be provisioned
    preexisting_db = (work_dir / ".env").exists()

    install_skill(verbose=verbose)
    try:
        stdout, stderr, elapsed = run_skill(persona, work_dir, verbose=verbose)
        ended_at = datetime.now().isoformat()
        gates = validate_gates(persona, work_dir, elapsed)
    finally:
        if not keep_skill:
            uninstall_skill(verbose=verbose)

    run = RunResult(
        persona_id=persona_id,
        started_at=started_at,
        ended_at=ended_at,  # type: ignore[possibly-undefined]
        total_seconds=elapsed,  # type: ignore[possibly-undefined]
        gates=gates,  # type: ignore[possibly-undefined]
        work_dir=str(work_dir),
        stdout=stdout,  # type: ignore[possibly-undefined]
        stderr=stderr,  # type: ignore[possibly-undefined]
    )

    result_path = save_results(run)

    # Derive the stem used for results files
    ts = result_path.stem  # e.g. alex_beginner_20260420_123456

    # Always capture a DB snapshot for post-run inspection
    snapshot_path = capture_db_snapshot(work_dir, ts, verbose=verbose)
    if snapshot_path:
        print(f"[Runner] DB snapshot saved: {snapshot_path.name}")

    # Post-run DB cleanup
    instance_id = _read_instance_id(work_dir)
    if preexisting_db:
        # Restore pre-existing DB to clean state for the next run
        env_path = work_dir / ".env"
        if env_path.exists():
            print("[Runner] Restoring pre-existing database to clean state...")
            wipe_database(env_path, verbose=verbose)
    elif instance_id and delete_db:
        print(f"[Runner] Deleting provisioned Aura instance {instance_id}...")
        delete_aura_instance(instance_id, verbose=verbose)
    elif instance_id:
        print(f"[Runner] Provisioned instance {instance_id} kept (pass --delete-db to remove)")

    print_report(run)
    print(f"[Runner] Results saved: {result_path}")
    print(f"[Runner] Work dir kept for inspection: {work_dir}")

    return run


def main():
    parser = argparse.ArgumentParser(description="Getting-Started Skill Test Runner")
    parser.add_argument("--persona", help="Path to persona YAML file")
    parser.add_argument("--all-personas", action="store_true", help="Run all personas")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--keep-skill", action="store_true",
                        help="Leave skill installed after run (for debugging)")
    parser.add_argument("--fixture", metavar="DIR",
                        help="Pre-populate work dir with files from this fixture directory (for resuming mid-flow)")
    parser.add_argument("--delete-db", action="store_true",
                        help="Delete a provisioned Aura instance after the run (snapshot is always saved first)")
    args = parser.parse_args()

    personas_dir = Path(__file__).parent.parent / "personas"

    if args.all_personas:
        persona_files = sorted(personas_dir.glob("*.yml"))
        runs = []
        for pf in persona_files:
            run = run_persona(str(pf), verbose=args.verbose, keep_skill=args.keep_skill,
                              delete_db=args.delete_db)
            runs.append(run)

        # Summary
        print("\n=== SUMMARY ===")
        for run in runs:
            status = "PASS" if run.passed else "FAIL"
            print(f"  {status}  {run.persona_id:<30} {run.gate_summary}  ({run.total_seconds:.1f}s)")
        total_pass = sum(1 for r in runs if r.passed)
        print(f"\n{total_pass}/{len(runs)} personas passed")

    elif args.persona:
        run = run_persona(args.persona, verbose=args.verbose, keep_skill=args.keep_skill,
                          fixture_dir=args.fixture, delete_db=args.delete_db)
        sys.exit(0 if run.passed else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
