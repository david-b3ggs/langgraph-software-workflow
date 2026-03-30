#!/usr/bin/env python3
"""CLI entrypoint for the ingestion pipeline (Phase 0).

Runs once per repo to generate the four MD context files that the dev loop depends on.
Skips if MD files already exist and are current (hash check — Phase 2+).

Usage:
    python scripts/run_ingestion.py --repo-path /path/to/your/repo
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.graphs.ingestion_graph import compile_ingestion
from src.state.ingestion_state import DEFAULT_INGESTION_STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_ingestion")


async def run(repo_path: str) -> None:
    logger.info("Starting ingestion  repo_path=%s", repo_path)
    app = compile_ingestion()
    initial_state = {**DEFAULT_INGESTION_STATE, "repo_path": repo_path}
    result = await app.ainvoke(initial_state)

    print("\n[INGESTION COMPLETE]")
    print(f"  ingestion_complete: {result.get('ingestion_complete')}")
    print(f"  MD files written to: {repo_path}")

    md_files = ["PROJECT.md", "CODE_STYLES.md", "BRAND_STYLES.md", "TESTING.md"]
    for f in md_files:
        p = Path(repo_path) / f
        status = "written" if p.exists() else "missing"
        print(f"    {f}: {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the repo ingestion pipeline.")
    parser.add_argument("--repo-path", required=True, help="Absolute path to the target repo")
    args = parser.parse_args()
    asyncio.run(run(str(Path(args.repo_path).resolve())))


if __name__ == "__main__":
    main()
