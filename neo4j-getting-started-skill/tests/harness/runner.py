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
import shutil
import subprocess
import sys
import time
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

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
    gates: list[GateResult] = field(default_factory=list)
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

    cmd = [
        "claude",
        "--print",                          # non-interactive
        "--dangerously-skip-permissions",   # no approval prompts
        "--output-format", "stream-json",   # stream events as they arrive
        "--verbose",                        # required for stream-json
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
        for raw in src:
            buf.write(raw)
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            t = ev.get("type", "")
            if t == "assistant":
                for block in ev.get("message", {}).get("content", []):
                    bt = block.get("type")
                    if bt == "text":
                        sys.stdout.write(block["text"])
                        sys.stdout.flush()
                    elif bt == "tool_use":
                        name = block.get("name", "?")
                        inp = str(block.get("input", ""))[:120]
                        sys.stdout.write(f"\n  [tool] {name}  {inp}\n")
                        sys.stdout.flush()
            elif t == "result":
                cost = ev.get("total_cost_usd")
                turns = ev.get("num_turns")
                cost_str = f"  cost=${cost:.4f}" if cost else ""
                sys.stdout.write(f"\n[Runner] done — turns={turns}{cost_str}\n")
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


def validate_gates(persona: dict, work_dir: Path, elapsed: float) -> list[GateResult]:
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
    out_path = RESULTS_DIR / f"{run.persona_id}_{ts}.json"
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
        }, f, indent=2)
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
                fixture_dir: str | None = None) -> RunResult:
    persona = load_persona(persona_path)
    persona_id = persona["persona"]["id"]

    # Fresh temp dir — Claude runs here; all generated files stay isolated
    work_dir = Path(tempfile.mkdtemp(prefix=f"neo4j_skill_{persona_id}_"))
    started_at = datetime.now().isoformat()

    print(f"\n[Runner] Starting persona: {persona_id}")
    print(f"[Runner] Work dir: {work_dir}")

    # Copy fixture files first (progress.md, schema.*, etc.) if provided
    if fixture_dir:
        fixture_path = Path(fixture_dir)
        for f in fixture_path.iterdir():
            if f.is_file():
                shutil.copy(str(f), str(work_dir / f.name))
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
    args = parser.parse_args()

    personas_dir = Path(__file__).parent.parent / "personas"

    if args.all_personas:
        persona_files = sorted(personas_dir.glob("*.yml"))
        runs = []
        for pf in persona_files:
            run = run_persona(str(pf), verbose=args.verbose, keep_skill=args.keep_skill)
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
                          fixture_dir=args.fixture)
        sys.exit(0 if run.passed else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
