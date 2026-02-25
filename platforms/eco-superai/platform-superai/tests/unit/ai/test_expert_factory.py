"""Unit tests for AI expert factory."""
from __future__ import annotations

import pytest

from src.ai.factory.expert_factory import ExpertFactory


class TestExpertFactory:
    def setup_method(self):
        self.factory = ExpertFactory()

    @pytest.mark.asyncio
    async def test_create_expert(self):
        expert = await self.factory.create_expert(
            name="Test Expert",
            domain="quantum",
            specialization="VQE",
            knowledge_base=[],
            model="gpt-4",
            temperature=0.7,
            system_prompt="",
        )
        assert expert["name"] == "Test Expert"
        assert expert["domain"] == "quantum"
        assert "id" in expert

    @pytest.mark.asyncio
    async def test_create_expert_with_custom_prompt(self):
        expert = await self.factory.create_expert(
            name="Custom",
            domain="custom",
            specialization="",
            knowledge_base=[],
            model="gpt-4",
            temperature=0.5,
            system_prompt="You are a custom expert.",
        )
        assert expert["system_prompt"] == "You are a custom expert."

    @pytest.mark.asyncio
    async def test_list_experts(self):
        await self.factory.create_expert(
            name="E1", domain="ml", specialization="", knowledge_base=[],
            model="gpt-4", temperature=0.7, system_prompt="",
        )
        experts = await self.factory.list_experts()
        assert len(experts) >= 1

    @pytest.mark.asyncio
    async def test_list_experts_by_domain(self):
        await self.factory.create_expert(
            name="ML Expert", domain="ml_filter_test", specialization="", knowledge_base=[],
            model="gpt-4", temperature=0.7, system_prompt="",
        )
        await self.factory.create_expert(
            name="QC Expert", domain="quantum_filter_test", specialization="", knowledge_base=[],
            model="gpt-4", temperature=0.7, system_prompt="",
        )
        ml_experts = await self.factory.list_experts(domain="ml_filter_test")
        assert all(e["domain"] == "ml_filter_test" for e in ml_experts)

    @pytest.mark.asyncio
    async def test_delete_expert(self):
        expert = await self.factory.create_expert(
            name="ToDelete", domain="test", specialization="", knowledge_base=[],
            model="gpt-4", temperature=0.7, system_prompt="",
        )
        await self.factory.delete_expert(expert["id"])
        experts = await self.factory.list_experts(domain="test")
        assert not any(e["id"] == expert["id"] for e in experts)

    @pytest.mark.asyncio
    async def test_query_nonexistent_expert(self):
        result = await self.factory.query_expert(
            expert_id="nonexistent",
            query="test",
            context={},
            max_tokens=100,
            include_sources=False,
        )
        assert "error" in result