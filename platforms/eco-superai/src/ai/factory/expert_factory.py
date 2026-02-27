
"""AI Expert Factory - Create and manage domain-specific AI experts."""
from __future__ import annotations

import uuid
import time
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

_EXPERT_STORE: dict[str, dict[str, Any]] = {}


class ExpertFactory:
    """Factory for creating domain-specific AI experts with RAG capabilities."""

    async def create_expert(self, name: str, domain: str, specialization: str,
                            knowledge_base: list[str], model: str, temperature: float, system_prompt: str) -> dict[str, Any]:
        expert_id = str(uuid.uuid4())

        default_prompts = {
            "quantum": "You are a quantum computing expert specializing in Qiskit, VQE, QAOA, and quantum error correction.",
            "ml": "You are a machine learning expert with deep knowledge of scikit-learn, TensorFlow, and PyTorch.",
            "devops": "You are a DevOps expert specializing in Kubernetes, ArgoCD, Helm, CI/CD pipelines, and cloud-native architecture.",
            "security": "You are a cybersecurity expert focusing on application security, OWASP, and zero-trust architecture.",
            "data_engineering": "You are a data engineering expert specializing in ETL pipelines, data warehousing, and real-time streaming.",
        }

        final_prompt = system_prompt or default_prompts.get(domain, f"You are an expert in {domain}.")
        if specialization:
            final_prompt += f"\nSpecialization: {specialization}"

        expert = {
            "id": expert_id,
            "name": name,
            "domain": domain,
            "specialization": specialization,
            "model": model,
            "temperature": temperature,
            "system_prompt": final_prompt,
            "knowledge_base": knowledge_base,
            "created_at": time.time(),
            "query_count": 0,
        }
        _EXPERT_STORE[expert_id] = expert
        logger.info("expert_created", expert_id=expert_id, name=name, domain=domain)
        return expert

    async def query_expert(self, expert_id: str, query: str, context: dict[str, Any],
                           max_tokens: int, include_sources: bool) -> dict[str, Any]:
        if expert_id not in _EXPERT_STORE:
            return {"error": f"Expert {expert_id} not found"}

        expert = _EXPERT_STORE[expert_id]
        expert["query_count"] += 1
        start = time.perf_counter()

        # RAG: retrieve relevant context from vector DB
        retrieved_context = []
        if expert["knowledge_base"]:
            try:
                from src.ai.vectordb.manager import VectorDBManager
                manager = VectorDBManager()
                for collection_id in expert["knowledge_base"][:3]:
                    results = await manager.search(collection=collection_id, query=query, top_k=3)
                    if "results" in results:
                        retrieved_context.extend(results["results"])
            except Exception as e:
                logger.warning("rag_retrieval_failed", error=str(e))

        # Build prompt with context
        messages = [{"role": "system", "content": expert["system_prompt"]}]
        if retrieved_context:
            ctx_text = "\n\n".join([r.get("document", "") for r in retrieved_context[:5]])
            messages.append({"role": "system", "content": f"Relevant context:\n{ctx_text}"})
        if context:
            messages.append({"role": "system", "content": f"Additional context: {context}"})
        messages.append({"role": "user", "content": query})

        # Call LLM
        try:
            from openai import AsyncOpenAI
            from src.infrastructure.config import get_settings
            settings = get_settings()
            client = AsyncOpenAI(api_key=settings.ai.openai_api_key)
            response = await client.chat.completions.create(
                model=expert["model"],
                messages=messages,
                max_tokens=max_tokens,
                temperature=expert["temperature"],
            )
            answer = response.choices[0].message.content
            usage = {"prompt_tokens": response.usage.prompt_tokens, "completion_tokens": response.usage.completion_tokens, "total_tokens": response.usage.total_tokens}
        except Exception as e:
            answer = f"[LLM unavailable] Expert '{expert['name']}' ({expert['domain']}): Based on domain knowledge, here is a synthesized response to your query about: {query[:200]}. Error: {str(e)}"
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        elapsed = (time.perf_counter() - start) * 1000

        result: dict[str, Any] = {
            "expert_id": expert_id,
            "expert_name": expert["name"],
            "domain": expert["domain"],
            "answer": answer,
            "usage": usage,
            "execution_time_ms": round(elapsed, 2),
        }
        if include_sources and retrieved_context:
            result["sources"] = retrieved_context[:5]
        return result

    async def list_experts(self, domain: str | None = None) -> list[dict[str, Any]]:
        experts = list(_EXPERT_STORE.values())
        if domain:
            experts = [e for e in experts if e["domain"] == domain]
        return [{k: v for k, v in e.items() if k != "system_prompt"} for e in experts]

    async def delete_expert(self, expert_id: str) -> dict[str, Any]:
        removed = _EXPERT_STORE.pop(expert_id, None)
        if removed is None:
            return {"status": "not_found", "expert_id": expert_id}
        logger.info("expert_deleted", expert_id=expert_id)
        return {"status": "deleted", "expert_id": expert_id, "name": removed.get("name", "")}

    def clear_experts(self) -> None:
        _EXPERT_STORE.clear()
def clear_experts() -> None:
    """Clear all experts from the store. For testing purposes."""
    _EXPERT_STORE.clear()
