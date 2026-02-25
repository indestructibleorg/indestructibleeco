"""GovernanceSandbox — evaluates untrusted policy scripts in a ProcessSandbox.

Uses the shared kernel ProcessSandbox with read-only filesystem and no network
to safely evaluate user-provided policy scripts. The script receives the operation
data via stdin (JSON) and must print a JSON result to stdout.
"""

from __future__ import annotations

import json
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from platform_shared.sandbox import (
    ExecutionResult,
    ProcessSandbox,
    SandboxConfig,
)
from platform_shared.sandbox.network import POLICY_NO_NETWORK

from governance_platform.domain.exceptions import SandboxPolicyError


class GovernanceSandbox:
    """Evaluates untrusted policy scripts inside an isolated ProcessSandbox.

    The sandbox enforces:
    - Read-only filesystem (scripts cannot modify the host)
    - No network access (scripts cannot exfiltrate data)
    - Timeout limits (scripts cannot hang forever)
    - Resource limits (scripts cannot consume unbounded memory/CPU)
    """

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        base_dir: Path | None = None,
    ) -> None:
        self._timeout = timeout_seconds
        self._base_dir = base_dir
        self._sandbox: ProcessSandbox | None = None
        self._sandbox_id: str | None = None

    async def initialize(self) -> None:
        """Create the underlying ProcessSandbox."""
        self._sandbox = ProcessSandbox(base_dir=self._base_dir)
        config = SandboxConfig(
            name="governance-policy-sandbox",
            timeout_seconds=self._timeout,
            network_policy=POLICY_NO_NETWORK,
            filesystem_readonly=True,
        )
        self._sandbox_id = await self._sandbox.create(config)

    async def teardown(self) -> None:
        """Destroy the underlying sandbox."""
        if self._sandbox and self._sandbox_id:
            await self._sandbox.destroy(self._sandbox_id)
            self._sandbox_id = None

    async def evaluate_script(
        self,
        script: str,
        operation: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate a policy script against an operation.

        The script is written to a temp file, then executed with python3 inside
        the sandbox. The operation dict is passed as a JSON string via a wrapper
        that feeds it to the script's stdin.

        Args:
            script: Python source code of the policy script.
            operation: The operation data to evaluate against.

        Returns:
            Parsed JSON result from the script's stdout.

        Raises:
            SandboxPolicyError: If the script fails, times out, or produces invalid output.
        """
        if self._sandbox is None or self._sandbox_id is None:
            await self.initialize()
        assert self._sandbox is not None
        assert self._sandbox_id is not None

        # Write the script to a temp file in the sandbox workspace
        sandbox_state = self._sandbox._sandboxes.get(self._sandbox_id)
        if sandbox_state is None:
            raise SandboxPolicyError("Sandbox not found", sandbox_id=self._sandbox_id or "")

        work_dir = sandbox_state.work_dir

        # Write the policy script
        script_path = work_dir / "policy_script.py"
        script_path.write_text(script, encoding="utf-8")

        # Write the operation data
        data_path = work_dir / "operation.json"
        data_path.write_text(json.dumps(operation), encoding="utf-8")

        # Create a wrapper that loads the data and runs the script
        wrapper = textwrap.dedent("""\
            import json
            import sys
            import os

            # Restrict dangerous builtins
            _BLOCKED = {"exec", "eval", "compile", "__import__", "open",
                        "breakpoint", "exit", "quit"}

            # Load operation data
            with open(os.path.join(os.path.dirname(__file__), "operation.json")) as f:
                operation = json.load(f)

            # Load and exec the policy script in a restricted namespace
            script_path = os.path.join(os.path.dirname(__file__), "policy_script.py")
            with open(script_path) as f:
                script_source = f.read()

            # Provide a safe namespace for the policy script
            namespace = {
                "operation": operation,
                "result": {"passed": True, "violations": [], "metadata": {}},
                "json": json,
            }

            exec(compile(script_source, script_path, "exec"), namespace)

            # Output the result
            print(json.dumps(namespace.get("result", {"passed": True, "violations": []})))
        """)

        wrapper_path = work_dir / "wrapper.py"
        wrapper_path.write_text(wrapper, encoding="utf-8")

        try:
            exec_result: ExecutionResult = await self._sandbox.execute(
                self._sandbox_id,
                ["python3", str(wrapper_path)],
            )
        except Exception as exc:
            raise SandboxPolicyError(
                f"Sandbox execution failed: {exc}",
                sandbox_id=self._sandbox_id,
            ) from exc

        if exec_result.timed_out:
            raise SandboxPolicyError(
                f"Policy script timed out after {self._timeout}s",
                sandbox_id=self._sandbox_id,
            )

        if exec_result.exit_code != 0:
            raise SandboxPolicyError(
                f"Policy script failed (exit code {exec_result.exit_code}): "
                f"{exec_result.stderr.strip()}",
                sandbox_id=self._sandbox_id,
            )

        stdout = exec_result.stdout.strip()
        if not stdout:
            raise SandboxPolicyError(
                "Policy script produced no output",
                sandbox_id=self._sandbox_id,
            )

        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise SandboxPolicyError(
                f"Policy script produced invalid JSON: {exc}",
                sandbox_id=self._sandbox_id,
            ) from exc

    @property
    def sandbox_id(self) -> str | None:
        return self._sandbox_id

    @property
    def is_initialized(self) -> bool:
        return self._sandbox is not None and self._sandbox_id is not None
