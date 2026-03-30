#!/usr/bin/env python3
"""CLI entrypoint for the multi-agent dev loop.

Usage:
    python scripts/run_dev_loop.py --task '{"title":"add login","type":"feature","scope":"backend"}'
    python scripts/run_dev_loop.py --task task.json
"""
import argparse
import asyncio
import json
import logging
import sys
import uuid
from pathlib import Path

# Ensure src/ is importable from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph.types import Command
from src.graphs.dev_loop_graph import compile_dev_loop, build_checkpointer
from src.state.dev_loop_state import DEFAULT_STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_dev_loop")


def load_task(raw: str) -> dict:
    """Accept a JSON string or a path to a JSON file."""
    p = Path(raw)
    if p.exists():
        return json.loads(p.read_text())
    return json.loads(raw)


def print_plan(plan: list | None) -> None:
    if not plan:
        print("\n[PLAN] (empty)")
        return
    print("\n[PLAN]")
    for t in plan:
        deps = ", ".join(t["depends_on"]) or "none"
        print(f"  [{t['id']}] type={t['type']}  depends_on={deps}")
        print(f"        hint: {t['context_hint']}")


async def run(args: argparse.Namespace) -> None:
    task = load_task(args.task)
    thread_id = args.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    logger.info("Starting dev loop  thread_id=%s  task=%s", thread_id, task.get("title"))

    checkpointer = await build_checkpointer(db_path=args.db)
    app = compile_dev_loop(checkpointer=checkpointer)

    # --- First invoke: runs until interrupt() in human_gate ---
    initial_state = {**DEFAULT_STATE, "task": task}
    result = await app.ainvoke(initial_state, config=config)

    # Surface the plan produced by the planner
    print_plan(result.get("plan"))

    # --- Human approval ---
    print("\nApprove plan to begin parallel execution? [y/n]: ", end="", flush=True)
    answer = input().strip().lower()
    approved = answer == "y"

    if not approved:
        print("Plan rejected. Exiting.")
        return

    # --- Resume: Command(resume=True) replays from the interrupt() call ---
    logger.info("Resuming graph after human approval  thread_id=%s", thread_id)
    final = await app.ainvoke(Command(resume=approved), config=config)

    print("\n[DONE]")
    print(f"  escalated:      {final.get('escalated', False)}")
    print(f"  worker_outputs: {list(final.get('worker_outputs', {}).keys())}")
    print(f"  review_passed:  {final.get('review_result', {}).get('passed') if final.get('review_result') else 'n/a'}")
    print(f"  tests_passed:   {final.get('test_result', {}).get('passed') if final.get('test_result') else 'n/a'}")
    print(f"\nThread ID (for resuming): {thread_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the multi-agent dev loop.")
    parser.add_argument("--task", required=True, help="Task as JSON string or path to JSON file")
    parser.add_argument("--thread-id", default=None, help="Thread ID for resuming a run")
    parser.add_argument("--db", default=None, help="Path to checkpoints SQLite DB")
    asyncio.run(run(parser.parse_args()))


if __name__ == "__main__":
    main()
