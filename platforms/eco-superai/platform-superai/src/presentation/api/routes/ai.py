"""AI & ML API routes -- Expert Factory, Vector DB, Agents, Embeddings."""
from __future__ import annotations

import structlog
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, Field

from src.application.services import AuditService
from src.application.use_cases.ai_management import (
    CreateExpertUseCase,
    CreateVectorCollectionUseCase,
    DeleteExpertUseCase,
    ExecuteAgentTaskUseCase,
    GenerateEmbeddingsUseCase,
    ListExpertsUseCase,
    ListVectorCollectionsUseCase,
    QueryExpertUseCase,
    SearchVectorCollectionUseCase,
)
from src.domain.value_objects.role import Permission
from src.presentation.api.dependencies import (
    get_client_ip,
    get_current_user,
    require_permission,
)
from src.presentation.api.schemas import (
    EmbeddingRequest,
    ExpertCreateRequest,
    ExpertQueryRequest,
    VectorSearchRequest,
    VectorStoreRequest,
)

logger = structlog.get_logger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Response schemas local to this router
# ---------------------------------------------------------------------------


class ExpertResponse(BaseModel):
    """AI expert descriptor."""
    expert_id: str
    name: str
    domain: str
    specialization: str = ""
    model: str = ""
    status: str = "active"
    created_at: str | None = None


class ExpertQueryResponse(BaseModel):
    """Response from querying an AI expert."""
    expert_id: str
    query: str
    response: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    model: str = ""
    tokens_used: int = 0
    latency_ms: float = 0.0


class ExpertListResponse(BaseModel):
    """List of AI experts."""
    items: list[ExpertResponse]
    total: int


class VectorUpsertResponse(BaseModel):
    """Confirmation of vector upsert."""
    collection: str
    document_count: int
    status: str = "success"


class VectorSearchResultResponse(BaseModel):
    """Vector search results."""
    collection: str
    results: list[dict[str, Any]]
    total: int
    query: str


class CollectionResponse(BaseModel):
    """Vector collection descriptor."""
    name: str
    document_count: int = 0
    embedding_model: str = ""


class AgentTaskRequest(BaseModel):
    """Request body for executing an agent task."""
    agent_type: str = Field(
        ...,
        pattern=r"^(code_generator|code_reviewer|test_writer|doc_writer|devops_automator|security_auditor)$",
    )
    task: str = Field(..., min_length=1, max_length=10000)
    context: dict[str, Any] = Field(default_factory=dict)
    constraints: list[str] = Field(default_factory=list)
    output_format: str = Field(default="markdown", pattern=r"^(markdown|json|code|yaml)$")


class AgentTaskResponse(BaseModel):
    """Agent task execution result."""
    task_id: str = ""
    agent_type: str
    status: str = "completed"
    output: str = ""
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class EmbeddingResponse(BaseModel):
    """Embedding generation result."""
    model: str
    embeddings: list[list[float]]
    total_tokens: int = 0


# ---------------------------------------------------------------------------
# Expert endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/experts",
    response_model=ExpertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new AI expert",
)
async def create_expert(
    body: ExpertCreateRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_MANAGE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Provision a new domain-specific AI expert with optional knowledge base
    and custom system prompt.

    Requires ``ai:manage`` permission.
    """
    use_case = CreateExpertUseCase()
    result = await use_case.execute(
        owner_id=current_user["user_id"],
        name=body.name,
        domain=body.domain,
        specialization=body.specialization,
        model=body.model,
        temperature=body.temperature,
        system_prompt=body.system_prompt,
        knowledge_base=body.knowledge_base,
    )
    await AuditService.log(
        action="ai.expert_created",
        resource_type="AIExpert",
        resource_id=result.get("expert_id"),
        user_id=current_user["user_id"],
        details={"name": body.name, "domain": body.domain, "model": body.model},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/experts/{expert_id}/query",
    response_model=ExpertQueryResponse,
    summary="Query an AI expert",
)
async def query_expert(
    expert_id: str,
    body: ExpertQueryRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_EXECUTE)),
) -> dict[str, Any]:
    """Send a query to an existing AI expert.  The expert may use
    retrieval-augmented generation (RAG) to enhance its response.

    Requires ``ai:execute`` permission.
    """
    use_case = QueryExpertUseCase()
    result = await use_case.execute(
        expert_id=expert_id,
        query=body.query,
        context=body.context,
        max_tokens=body.max_tokens,
        include_sources=body.include_sources,
    )
    return result


@router.get(
    "/experts",
    response_model=ExpertListResponse,
    summary="List AI experts",
)
async def list_experts(
    domain: str | None = Query(None, description="Filter by domain"),
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_READ)),
) -> dict[str, Any]:
    """List all registered AI experts, optionally filtered by domain.

    Requires ``ai:read`` permission.
    """
    use_case = ListExpertsUseCase()
    items = await use_case.execute()
    if domain:
        items = [e for e in items if e.get("domain") == domain]
    return {"items": items, "total": len(items)}


@router.get(
    "/experts/{expert_id}",
    response_model=ExpertResponse,
    summary="Get a specific AI expert",
)
async def get_expert(
    expert_id: str,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_READ)),
) -> dict[str, Any]:
    """Get the details of a specific AI expert by ID.

    Requires ``ai:read`` permission.
    """
    use_case = ListExpertsUseCase()
    items = await use_case.execute()
    for item in items:
        if item.get("expert_id") == expert_id:
            return item
    from src.domain.exceptions import EntityNotFoundException
    raise EntityNotFoundException("AIExpert", expert_id)


@router.delete(
    "/experts/{expert_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an AI expert",
)
async def delete_expert(
    expert_id: str,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_MANAGE)),
    client_ip: str = Depends(get_client_ip),
) -> None:
    """Remove an AI expert and its associated resources.

    Requires ``ai:manage`` permission.
    """
    use_case = DeleteExpertUseCase()
    await use_case.execute(expert_id=expert_id)
    await AuditService.log(
        action="ai.expert_deleted",
        resource_type="AIExpert",
        resource_id=expert_id,
        user_id=current_user["user_id"],
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )


# ---------------------------------------------------------------------------
# Vector store endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/vectors/upsert",
    response_model=VectorUpsertResponse,
    summary="Upsert documents into a vector collection",
)
async def vector_upsert(
    body: VectorStoreRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Embed and store documents into a named vector collection.  Creates the
    collection if it does not exist.

    Requires ``ai:execute`` permission.
    """
    use_case = CreateVectorCollectionUseCase()
    result = await use_case.execute(
        collection=body.collection,
        documents=body.documents,
        metadatas=body.metadatas,
        ids=body.ids,
    )
    await AuditService.log(
        action="ai.vector_upsert",
        resource_type="VectorCollection",
        resource_id=body.collection,
        user_id=current_user["user_id"],
        details={"document_count": len(body.documents)},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


@router.post(
    "/vectors/search",
    response_model=VectorSearchResultResponse,
    summary="Semantic search in a vector collection",
)
async def vector_search(
    body: VectorSearchRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_READ)),
) -> dict[str, Any]:
    """Perform a semantic similarity search across a vector collection.

    Requires ``ai:read`` permission.
    """
    use_case = SearchVectorCollectionUseCase()
    result = await use_case.execute(
        collection=body.collection,
        query=body.query,
        top_k=body.top_k,
        threshold=body.threshold,
    )
    return result


@router.get(
    "/vectors/collections",
    response_model=list[CollectionResponse],
    summary="List vector collections",
)
async def list_collections(
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_READ)),
) -> Any:
    """List all vector collections available in the platform.

    Requires ``ai:read`` permission.
    """
    use_case = ListVectorCollectionsUseCase()
    result = await use_case.execute()
    # The use case may return a dict with a "collections" key or a list directly.
    if isinstance(result, dict):
        return result.get("collections", [])
    return result


@router.delete(
    "/vectors/collections/{collection}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a vector collection",
)
async def delete_collection(
    collection: str,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_MANAGE)),
    client_ip: str = Depends(get_client_ip),
) -> None:
    """Delete a vector collection and all its documents.

    Requires ``ai:manage`` permission.
    """
    from src.ai.vectordb.manager import VectorDBManager
    manager = VectorDBManager()
    await manager.delete_collection(collection)
    await AuditService.log(
        action="ai.collection_deleted",
        resource_type="VectorCollection",
        resource_id=collection,
        user_id=current_user["user_id"],
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )


# ---------------------------------------------------------------------------
# Agent endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/agents/execute",
    response_model=AgentTaskResponse,
    summary="Execute an automated agent task",
)
async def execute_agent_task(
    body: AgentTaskRequest,
    request: Request,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_EXECUTE)),
    client_ip: str = Depends(get_client_ip),
) -> dict[str, Any]:
    """Dispatch a task to a specialised autonomous agent (code generation,
    review, testing, documentation, DevOps automation, or security audit).

    Requires ``ai:execute`` permission.
    """
    use_case = ExecuteAgentTaskUseCase()
    result = await use_case.execute(
        agent_type=body.agent_type,
        task=body.task,
        context=body.context,
        constraints=body.constraints,
        output_format=body.output_format,
    )
    await AuditService.log(
        action="ai.agent_executed",
        resource_type="AgentTask",
        resource_id=result.get("task_id"),
        user_id=current_user["user_id"],
        details={"agent_type": body.agent_type, "output_format": body.output_format},
        ip_address=client_ip,
        user_agent=request.headers.get("User-Agent"),
    )
    return result


# ---------------------------------------------------------------------------
# Embedding endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/embeddings",
    response_model=EmbeddingResponse,
    summary="Generate text embeddings",
)
async def generate_embeddings(
    body: EmbeddingRequest,
    current_user: dict[str, Any] = Depends(require_permission(Permission.AI_EXECUTE)),
) -> dict[str, Any]:
    """Generate vector embeddings for the given text inputs.

    Requires ``ai:execute`` permission.
    """
    use_case = GenerateEmbeddingsUseCase()
    return await use_case.execute(texts=body.texts, model=body.model)
