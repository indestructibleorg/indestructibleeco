"""AI expert and vector store management use cases."""
from __future__ import annotations

from typing import Any

import structlog

from src.application.events import get_event_bus
from src.domain.entities.ai_expert import AIExpert, ExpertDomain

logger = structlog.get_logger(__name__)


class CreateExpertUseCase:
    """Create a new domain-specific AI expert."""

    def __init__(self) -> None:
        self._bus = get_event_bus()

    async def execute(
        self,
        owner_id: str,
        name: str,
        domain: str,
        specialization: str = "",
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        system_prompt: str = "",
        knowledge_base: list[str] | None = None,
    ) -> dict[str, Any]:
        from src.ai.factory.expert_factory import ExpertFactory
        factory = ExpertFactory()

        result = await factory.create_expert(
            name=name,
            domain=domain,
            specialization=specialization,
            knowledge_base=knowledge_base or [],
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )

        expert = AIExpert.create(
            name=name,
            domain=domain,
            owner_id=owner_id,
            specialization=specialization,
            model=model,
            temperature=temperature,
            system_prompt=system_prompt,
        )
        await self._bus.publish_all(expert.collect_events())

        logger.info("ai_expert_created", expert_id=result.get("expert_id"), name=name, domain=domain)
        return result


class QueryExpertUseCase:
    """Query an existing AI expert."""

    async def execute(
        self,
        expert_id: str,
        query: str,
        context: dict[str, Any] | None = None,
        max_tokens: int = 2000,
        include_sources: bool = False,
    ) -> dict[str, Any]:
        from src.ai.factory.expert_factory import ExpertFactory
        factory = ExpertFactory()

        result = await factory.query_expert(
            expert_id=expert_id,
            query=query,
            context=context or {},
            max_tokens=max_tokens,
            include_sources=include_sources,
        )

        logger.info("ai_expert_queried", expert_id=expert_id)
        return result


class ListExpertsUseCase:
    """List all registered AI experts."""

    async def execute(self) -> list[dict[str, Any]]:
        from src.ai.factory.expert_factory import ExpertFactory, _EXPERT_STORE
        return list(_EXPERT_STORE.values())


class DeleteExpertUseCase:
    """Remove an AI expert."""

    async def execute(self, expert_id: str) -> dict[str, Any]:
        from src.ai.factory.expert_factory import ExpertFactory
        factory = ExpertFactory()
        result = await factory.delete_expert(expert_id)
        logger.info("ai_expert_deleted", expert_id=expert_id)
        return result


# ---------------------------------------------------------------------------
# Vector Store Use Cases
# ---------------------------------------------------------------------------

class CreateVectorCollectionUseCase:
    """Create or add documents to a vector collection."""

    async def execute(
        self,
        collection: str,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> dict[str, Any]:
        from src.ai.vectordb.manager import VectorDBManager
        manager = VectorDBManager()
        result = await manager.add_documents(
            collection_name=collection,
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info("vector_collection_updated", collection=collection, doc_count=len(documents))
        return result


class SearchVectorCollectionUseCase:
    """Semantic search within a vector collection."""

    async def execute(
        self,
        collection: str,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> dict[str, Any]:
        from src.ai.vectordb.manager import VectorDBManager
        manager = VectorDBManager()
        result = await manager.semantic_search(
            collection_name=collection,
            query=query,
            top_k=top_k,
            threshold=threshold,
        )
        logger.info("vector_search_executed", collection=collection, top_k=top_k)
        return result


class ListVectorCollectionsUseCase:
    """List all vector collections."""

    async def execute(self) -> list[dict[str, Any]]:
        from src.ai.vectordb.manager import VectorDBManager
        manager = VectorDBManager()
        return await manager.list_collections()


class GenerateEmbeddingsUseCase:
    """Generate text embeddings."""

    async def execute(
        self,
        texts: list[str],
        model: str = "text-embedding-3-small",
    ) -> dict[str, Any]:
        from src.ai.embeddings.generator import EmbeddingGenerator
        generator = EmbeddingGenerator()
        result = await generator.generate(texts=texts, model=model)
        logger.info("embeddings_generated", count=len(texts), model=model)
        return result


class ExecuteAgentTaskUseCase:
    """Execute an automated agent task."""

    async def execute(
        self,
        agent_type: str,
        task: str,
        context: dict[str, Any] | None = None,
        constraints: list[str] | None = None,
        output_format: str = "markdown",
    ) -> dict[str, Any]:
        from src.ai.agents.task_executor import AgentTaskExecutor
        executor = AgentTaskExecutor()
        result = await executor.execute(
            agent_type=agent_type,
            task=task,
            context=context or {},
            constraints=constraints or [],
            output_format=output_format,
        )
        logger.info("agent_task_executed", agent_type=agent_type)
        return result


__all__ = [
    "CreateExpertUseCase",
    "QueryExpertUseCase",
    "ListExpertsUseCase",
    "DeleteExpertUseCase",
    "CreateVectorCollectionUseCase",
    "SearchVectorCollectionUseCase",
    "ListVectorCollectionsUseCase",
    "GenerateEmbeddingsUseCase",
    "ExecuteAgentTaskUseCase",
]