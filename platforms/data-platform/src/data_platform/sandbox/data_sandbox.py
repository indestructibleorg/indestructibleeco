"""DataSandbox — isolated data processing environment.

Wraps the shared kernel's ProcessSandbox to run untrusted data
transformations with memory limits and timeout enforcement.
"""

from __future__ import annotations

import json
import textwrap
import sys
from typing import Any

from platform_shared.sandbox.runtime import (
    ExecutionResult,
    ProcessSandbox,
    SandboxConfig,
    SandboxStatus,
)
from platform_shared.sandbox.resource import ResourceLimits


class DataSandbox:
    """Processes untrusted data transformations inside a ProcessSandbox.

    Provides a high-level API for executing Python transformation code
    against a data payload, with configurable resource limits.
    """

    def __init__(
        self,
        memory_mb: int = 256,
        timeout_seconds: float = 30.0,
        max_processes: int = 4,
    ) -> None:
        self._memory_mb = memory_mb
        self._timeout_seconds = timeout_seconds
        self._max_processes = max_processes
        self._sandbox = ProcessSandbox()
        self._sandbox_id: str | None = None

    async def initialize(self) -> None:
        """Provision the underlying sandbox."""
        config = SandboxConfig(
            name="data-sandbox",
            resource_limits=ResourceLimits(
                memory_mb=self._memory_mb,
                max_processes=self._max_processes,
            ),
            timeout_seconds=self._timeout_seconds,
        )
        self._sandbox_id = await self._sandbox.create(config)

    async def execute_transform(
        self,
        data: list[dict[str, Any]],
        transform_code: str,
    ) -> dict[str, Any]:
        """Execute a Python transformation on the given data inside the sandbox.

        The transform_code receives the data as a variable named ``data``
        and must assign its result to a variable named ``result``.

        Args:
            data: Input data rows.
            transform_code: Python code that reads ``data`` and writes ``result``.

        Returns:
            Dictionary with 'result', 'success', and execution metadata.
        """
        if self._sandbox_id is None:
            await self.initialize()

        # Build a self-contained script
        script = textwrap.dedent(f"""\
            import json, sys
            data = json.loads(sys.argv[1])
            result = None
            {textwrap.indent(transform_code, '            ').strip()}
            print(json.dumps({{"result": result, "count": len(data)}}))
        """)

        data_json = json.dumps(data)

        result: ExecutionResult = await self._sandbox.execute(
            self._sandbox_id,
            [sys.executable, "-c", script, data_json],
        )

        if result.success:
            try:
                output = json.loads(result.stdout.strip())
                return {
                    "success": True,
                    "result": output.get("result"),
                    "count": output.get("count", 0),
                    "duration_seconds": result.duration_seconds,
                }
            except (json.JSONDecodeError, ValueError):
                return {
                    "success": True,
                    "result": result.stdout.strip(),
                    "duration_seconds": result.duration_seconds,
                }
        else:
            return {
                "success": False,
                "error": result.stderr.strip() or "Execution failed",
                "exit_code": result.exit_code,
                "duration_seconds": result.duration_seconds,
            }

    async def get_status(self) -> str:
        """Return the sandbox status string."""
        if self._sandbox_id is None:
            return "not_initialized"
        status = await self._sandbox.get_status(self._sandbox_id)
        return status.value

    async def destroy(self) -> None:
        """Tear down the sandbox and reclaim resources."""
        if self._sandbox_id is not None:
            await self._sandbox.destroy(self._sandbox_id)
            self._sandbox_id = None
