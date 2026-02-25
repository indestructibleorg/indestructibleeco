"""Prompt template management — versioned, composable prompt engineering."""
from __future__ import annotations

import re
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class PromptTemplate:
    """A single prompt template with variable substitution."""

    def __init__(self, name: str, template: str, version: str = "1.0", description: str = "") -> None:
        self.name = name
        self.template = template
        self.version = version
        self.description = description
        self._variables = self._extract_variables(template)

    @property
    def variables(self) -> list[str]:
        return self._variables

    def render(self, **kwargs: Any) -> str:
        """Render template with variable substitution."""
        missing = [v for v in self._variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing template variables: {missing}")
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "template": self.template,
            "version": self.version,
            "description": self.description,
            "variables": self._variables,
        }

    @staticmethod
    def _extract_variables(template: str) -> list[str]:
        return list(dict.fromkeys(re.findall(r"\{\{(\w+)\}\}", template)))


class PromptTemplateManager:
    """Registry for managing prompt templates."""

    def __init__(self) -> None:
        self._templates: dict[str, PromptTemplate] = {}
        self._register_defaults()

    def register(self, template: PromptTemplate) -> None:
        self._templates[template.name] = template
        logger.debug("prompt_template_registered", name=template.name, version=template.version)

    def get(self, name: str) -> PromptTemplate | None:
        return self._templates.get(name)

    def render(self, name: str, **kwargs: Any) -> str:
        template = self._templates.get(name)
        if template is None:
            raise KeyError(f"Prompt template '{name}' not found")
        return template.render(**kwargs)

    def list_templates(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._templates.values()]

    def delete(self, name: str) -> bool:
        return self._templates.pop(name, None) is not None

    def _register_defaults(self) -> None:
        defaults = [
            PromptTemplate(
                name="code_review",
                template=(
                    "You are a senior software engineer performing a code review.\n\n"
                    "Language: {{language}}\n"
                    "Context: {{context}}\n\n"
                    "Code to review:\n```\n{{code}}\n```\n\n"
                    "Provide feedback on:\n"
                    "1. Correctness and potential bugs\n"
                    "2. Security vulnerabilities\n"
                    "3. Performance considerations\n"
                    "4. Code style and best practices\n"
                    "5. Suggested improvements"
                ),
                version="1.0",
                description="Code review prompt for any programming language",
            ),
            PromptTemplate(
                name="test_generation",
                template=(
                    "You are a test engineering expert.\n\n"
                    "Generate comprehensive tests for the following {{language}} code:\n"
                    "```\n{{code}}\n```\n\n"
                    "Framework: {{framework}}\n"
                    "Requirements:\n"
                    "- Cover happy path, edge cases, and error scenarios\n"
                    "- Use descriptive test names\n"
                    "- Include assertions with clear messages\n"
                    "- Aim for >90% coverage"
                ),
                version="1.0",
                description="Test generation prompt",
            ),
            PromptTemplate(
                name="documentation",
                template=(
                    "You are a technical writer creating documentation.\n\n"
                    "Subject: {{subject}}\n"
                    "Audience: {{audience}}\n"
                    "Format: {{format}}\n\n"
                    "Source material:\n{{content}}\n\n"
                    "Generate clear, comprehensive documentation including:\n"
                    "- Overview and purpose\n"
                    "- Key concepts\n"
                    "- Usage examples\n"
                    "- API reference (if applicable)\n"
                    "- Troubleshooting"
                ),
                version="1.0",
                description="Documentation generation prompt",
            ),
            PromptTemplate(
                name="rag_qa",
                template=(
                    "Answer the question based on the provided context.\n"
                    "If the context doesn't contain enough information, say so.\n\n"
                    "Context:\n{{context}}\n\n"
                    "Question: {{question}}\n\n"
                    "Provide a detailed, accurate answer with citations from the context."
                ),
                version="1.0",
                description="RAG question-answering prompt",
            ),
            PromptTemplate(
                name="quantum_analysis",
                template=(
                    "You are a quantum computing expert.\n\n"
                    "Algorithm: {{algorithm}}\n"
                    "Qubits: {{num_qubits}}\n"
                    "Results:\n{{results}}\n\n"
                    "Analyze the quantum computation results:\n"
                    "1. Interpret the measurement outcomes\n"
                    "2. Assess circuit fidelity\n"
                    "3. Suggest optimizations\n"
                    "4. Compare with classical alternatives"
                ),
                version="1.0",
                description="Quantum computation result analysis",
            ),
            PromptTemplate(
                name="security_audit",
                template=(
                    "You are a cybersecurity expert performing a security audit.\n\n"
                    "System: {{system}}\n"
                    "Scope: {{scope}}\n"
                    "Configuration:\n{{config}}\n\n"
                    "Perform a thorough security assessment:\n"
                    "1. Identify vulnerabilities (CVSS scoring)\n"
                    "2. Check OWASP Top 10 compliance\n"
                    "3. Review authentication and authorization\n"
                    "4. Assess data protection measures\n"
                    "5. Provide remediation recommendations with priority"
                ),
                version="1.0",
                description="Security audit prompt",
            ),
        ]
        for template in defaults:
            self.register(template)


# Singleton
_manager: PromptTemplateManager | None = None


def get_prompt_manager() -> PromptTemplateManager:
    global _manager
    if _manager is None:
        _manager = PromptTemplateManager()
    return _manager


__all__ = ["PromptTemplate", "PromptTemplateManager", "get_prompt_manager"]