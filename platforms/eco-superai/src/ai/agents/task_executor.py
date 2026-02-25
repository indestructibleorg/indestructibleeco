"""Automated Agent Task Executor - Code generation, review, testing, DevOps."""
from __future__ import annotations

import time
import uuid
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


AGENT_SYSTEM_PROMPTS = {
    "code_generator": "You are an expert code generator. Write clean, production-ready, well-documented code following best practices. Include type hints, error handling, and docstrings.",
    "code_reviewer": "You are a senior code reviewer. Analyze code for bugs, security vulnerabilities, performance issues, and adherence to best practices. Provide actionable feedback.",
    "test_writer": "You are a test engineering expert. Write comprehensive unit tests, integration tests, and edge case tests using pytest. Aim for high coverage.",
    "doc_writer": "You are a technical documentation expert. Write clear, comprehensive documentation including API docs, architecture guides, and runbooks.",
    "devops_automator": "You are a DevOps automation expert. Generate Kubernetes manifests, Helm charts, CI/CD pipelines, Terraform configs, and deployment scripts.",
    "security_auditor": "You are a security auditor. Analyze systems for vulnerabilities, compliance issues, and security best practices. Provide remediation steps.",
}


class AgentTaskExecutor:
    """Execute automated tasks using specialized AI agents."""

    async def execute(self, agent_type: str, task: str, context: dict[str, Any],
                      constraints: list[str], output_format: str) -> dict[str, Any]:
        start = time.perf_counter()
        task_id = str(uuid.uuid4())

        system_prompt = AGENT_SYSTEM_PROMPTS.get(agent_type, "You are a helpful AI assistant.")

        if constraints:
            system_prompt += "\n\nConstraints:\n" + "\n".join(f"- {c}" for c in constraints)

        format_instructions = {
            "markdown": "Format your response in Markdown.",
            "json": "Return your response as valid JSON.",
            "code": "Return only executable code with comments.",
            "yaml": "Return your response as valid YAML.",
        }
        system_prompt += f"\n\n{format_instructions.get(output_format, '')}"

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        messages.append({"role": "user", "content": task})

        # Execute via LLM
        try:
            from openai import AsyncOpenAI
            from src.infrastructure.config import get_settings
            settings = get_settings()
            client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
            response = await client.chat.completions.create(
                model=settings.ai.openai_model,
                messages=messages,
                max_tokens=settings.ai.max_tokens,
                temperature=0.3,
            )
            output = response.choices[0].message.content
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        except Exception as e:
            output = self._generate_fallback(agent_type, task, output_format)
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "fallback": True}

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("agent_task_completed", task_id=task_id, agent_type=agent_type, elapsed_ms=elapsed)

        return {
            "task_id": task_id,
            "agent_type": agent_type,
            "status": "completed",
            "output": output,
            "output_format": output_format,
            "usage": usage,
            "execution_time_ms": round(elapsed, 2),
        }

    def _generate_fallback(self, agent_type: str, task: str, output_format: str) -> str:
        """Generate a structured fallback when LLM is unavailable."""
        templates = {
            "code_generator": f'"""\nGenerated code stub for: {task[:100]}\nTODO: Implement with LLM assistance\n"""\n\ndef generated_function():\n    raise NotImplementedError("LLM unavailable - implement manually")\n',
            "code_reviewer": f"# Code Review Report\n\n## Task: {task[:100]}\n\n### Findings\n- [ ] Static analysis pending\n- [ ] Security scan pending\n- [ ] Performance review pending\n\n### Recommendation\nManual review required - LLM service unavailable.\n",
            "test_writer": f'"""Test suite stub for: {task[:100]}"""\nimport pytest\n\nclass TestGenerated:\n    def test_placeholder(self):\n        """TODO: Generate tests with LLM"""\n        pytest.skip("LLM unavailable")\n',
            "doc_writer": f"# Documentation\n\n## {task[:100]}\n\n> Auto-generation pending - LLM service unavailable.\n\n### Sections\n1. Overview\n2. Architecture\n3. API Reference\n4. Examples\n",
            "devops_automator": f"# DevOps Automation\n# Task: {task[:100]}\n# Status: LLM unavailable - manual configuration required\n\napiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: placeholder\nspec:\n  replicas: 1\n",
            "security_auditor": f"# Security Audit Report\n\n## Scope: {task[:100]}\n\n### Status: Pending\nAutomated audit requires LLM service.\n\n### Checklist\n- [ ] OWASP Top 10\n- [ ] Dependency vulnerabilities\n- [ ] Configuration review\n",
        }
        return templates.get(agent_type, f"Task: {task}\nStatus: LLM unavailable")