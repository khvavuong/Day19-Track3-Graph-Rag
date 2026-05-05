#!/usr/bin/env python3
"""
Orchestrate Day 19 GraphRAG workflow with optional Docker execution.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def run_cmd(cmd: list[str], cwd: Path) -> int:
    print(f"\n$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd)
    return proc.returncode


def run_inside_backend(compose_cmd: str, inner_cmd: list[str], cwd: Path) -> int:
    if compose_cmd == "docker-compose":
        cmd = ["docker-compose", "exec", "-T", "backend"] + inner_cmd
    else:
        cmd = ["docker", "compose", "exec", "-T", "backend"] + inner_cmd
    return run_cmd(cmd, cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 19 end-to-end pipeline runner")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root (contains docker-compose.yml)",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory path relative to project root",
    )
    parser.add_argument(
        "--compose-cmd",
        choices=["docker-compose", "docker compose"],
        default="docker-compose",
        help="Compose command style available in your environment",
    )
    parser.add_argument("--skip-up", action="store_true", help="Skip docker compose up")
    parser.add_argument(
        "--skip-benchmark", action="store_true", help="Skip benchmark phase"
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Ingest directory recursively"
    )
    parser.add_argument(
        "--benchmark-questions",
        type=Path,
        default=None,
        help="Optional questions file (.txt or .csv with question column)",
    )
    args = parser.parse_args()

    root = args.project_root.resolve()
    if not (root / "docker-compose.yml").exists():
        print(f"ERROR: docker-compose.yml not found at {root}")
        return 1

    env_map = parse_env_file(root / ".env")
    provider = env_map.get("LLM_PROVIDER", "openai").lower()
    if provider == "openai":
        api_key = env_map.get("OPENAI_API_KEY", "")
        if not api_key or "your_openai_api_key_here" in api_key:
            print("ERROR: OPENAI_API_KEY is missing/placeholder while LLM_PROVIDER=openai")
            return 1
        base_url = env_map.get("OPENAI_BASE_URL", "").strip()
        if base_url and base_url.startswith("sk-"):
            print("ERROR: OPENAI_BASE_URL looks like an API key. Put your key in OPENAI_API_KEY instead.")
            return 1

    neo_pass = env_map.get("NEO4J_PASSWORD", "")
    if not neo_pass:
        print("ERROR: NEO4J_PASSWORD is missing in .env")
        return 1
    if neo_pass.strip().lower() == "neo4j":
        print("ERROR: NEO4J_PASSWORD cannot be 'neo4j'. Choose a non-default password (e.g. graphrag_password).")
        return 1

    local_neo_uri = env_map.get("NEO4J_URI", "").strip()
    if local_neo_uri.startswith("bolt://neo4j:"):
        print(
            "ERROR: .env NEO4J_URI is set to bolt://neo4j:... which only resolves inside Docker network.\n"
            "Use bolt://localhost:7687 when running scripts on host."
        )
        return 1

    compose_up_cmd = (
        ["docker-compose", "up", "-d", "--build"]
        if args.compose_cmd == "docker-compose"
        else ["docker", "compose", "up", "-d", "--build"]
    )

    # 1) Optional: start stack
    if not args.skip_up:
        code = run_cmd(compose_up_cmd, root)
        if code != 0:
            return code

    # 2) Data precheck
    precheck_cmd = [
        "python",
        "scripts/day19_data_precheck.py",
        "--data-dir",
        str(args.data_dir),
    ]
    if args.recursive:
        precheck_cmd.append("--recursive")
    code = run_inside_backend(args.compose_cmd, precheck_cmd, root)
    if code not in (0, 2):
        return code

    # 3) Setup neo4j indexes + baseline stats
    code = run_inside_backend(
        args.compose_cmd, ["python", "scripts/setup_neo4j.py", "--test", "--setup", "--stats"], root
    )
    if code != 0:
        return code

    # 4) Ingest data
    ingest_cmd = [
        "python",
        "scripts/ingest_documents.py",
        "--input-dir",
        str(args.data_dir),
    ]
    if args.recursive:
        ingest_cmd.append("--recursive")
    code = run_inside_backend(args.compose_cmd, ingest_cmd, root)
    if code != 0:
        return code

    # 5) Post-ingest stats
    code = run_inside_backend(
        args.compose_cmd, ["python", "scripts/setup_neo4j.py", "--stats"], root
    )
    if code != 0:
        return code

    # 6) Benchmark
    if not args.skip_benchmark:
        bench_cmd = ["python", "scripts/day19_benchmark.py"]
        if args.benchmark_questions:
            bench_cmd += ["--questions-file", str(args.benchmark_questions)]
        code = run_inside_backend(args.compose_cmd, bench_cmd, root)
        if code != 0:
            return code

    print("\nDay 19 pipeline finished successfully.")
    print("Outputs:")
    print("- reports/day19_benchmark_results.csv")
    print("- reports/day19_benchmark_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
