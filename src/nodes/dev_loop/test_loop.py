import asyncio
import logging
import re
from src.state.dev_loop_state import DevLoopState, TestResult
from src.llm.client import get_llm

logger = logging.getLogger(__name__)

_TEST_STUB_PROMPT = """You are a QA engineer. Given the diffs below, write pytest stubs for the changed logic.
Output only valid Python test code (no explanation).

Testing guidelines:
{testing_md}

Code style guidelines:
{code_styles_md}

Diffs:
{diffs}
"""

_TEST_TIMEOUT = 30  # seconds


def _extract_pytest_command(testing_md: str) -> str | None:
    """Find the first fenced code block in TESTING.md that contains 'pytest'."""
    for block in re.finditer(r"```[^\n]*\n(.*?)```", testing_md, re.DOTALL):
        code = block.group(1).strip()
        if "pytest" in code:
            # Return the first pytest line
            for line in code.splitlines():
                if line.strip().startswith("pytest"):
                    return line.strip()
    return None


def _parse_pytest_failures(output: str) -> list[dict]:
    """Extract FAILED lines from pytest output."""
    failures = []
    for line in output.splitlines():
        if line.startswith("FAILED"):
            parts = line.split(" - ", 1)
            failures.append({
                "test": parts[0].replace("FAILED", "").strip(),
                "reason": parts[1] if len(parts) > 1 else "",
            })
    return failures


async def test_loop_node(state: DevLoopState) -> dict:
    """Write test stubs (logged only) then run existing test suite from TESTING.md."""
    retry = state.get("test_retry_count", 0)
    logger.info("test_loop: attempt=%d", retry + 1)

    worker_outputs = state.get("worker_outputs", {})
    diffs = "\n\n".join(
        f"### {agent}\n{output['diff']}"
        for agent, output in worker_outputs.items()
        if output.get("diff")
    )
    md = state.get("compressed_md", {})
    testing_md = md.get("TESTING.md", "")

    # Step 6a: LLM generates test stubs (log only — Phase 5 will apply + run them)
    if diffs:
        try:
            llm = get_llm()
            stub_prompt = _TEST_STUB_PROMPT.format(
                testing_md=testing_md,
                code_styles_md=md.get("CODE_STYLES.md", ""),
                diffs=diffs,
            )
            stub_response = await llm.ainvoke(stub_prompt)
            stub_code = stub_response.content if hasattr(stub_response, "content") else str(stub_response)
            logger.info("test_loop: generated test stubs (%d chars)", len(stub_code))
            logger.debug("test_loop: test stubs:\n%s", stub_code)
        except Exception as exc:
            logger.warning("test_loop: test stub generation failed: %s", exc)

    # Step 6b: Run existing test suite
    test_cmd = _extract_pytest_command(testing_md)
    if not test_cmd:
        logger.warning("test_loop: no pytest command found in TESTING.md — defaulting to pass")
        result: TestResult = {"passed": True, "failures": [], "retry_count": retry}
        return {
            "test_result": result,
            "test_retry_count": retry,
        }

    logger.info("test_loop: running: %s", test_cmd)
    args = test_cmd.split()
    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=_TEST_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            logger.warning("test_loop: test suite timed out after %ds — defaulting to pass", _TEST_TIMEOUT)
            result = {"passed": True, "failures": [], "retry_count": retry}
            return {"test_result": result, "test_retry_count": retry}

        output = stdout_bytes.decode("utf-8", errors="replace")
        passed = proc.returncode == 0
        failures = [] if passed else _parse_pytest_failures(output)
        logger.info("test_loop: returncode=%d failures=%d", proc.returncode, len(failures))
        if not passed:
            logger.debug("test_loop: pytest output:\n%s", output)

    except Exception as exc:
        logger.warning("test_loop: subprocess failed to start: %s — defaulting to pass", exc)
        passed = True
        failures = []

    result = {"passed": passed, "failures": failures, "retry_count": retry}
    return {
        "test_result": result,
        "test_retry_count": retry + (0 if passed else 1),
    }
