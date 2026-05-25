import logging
from typing import Any

from ms3.knowledge.service import knowledge_service

logger = logging.getLogger(__name__)


async def retrieve(
    kb_id: str,
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.5,
) -> list[dict]:
    from ms3.database.connection import async_session_factory
    from ms3.database.dal import KnowledgeBaseDAL

    try:
        async with async_session_factory() as session:
            kb_dal = KnowledgeBaseDAL(session=session, tenant_id=None)
            kb = await kb_dal.get(kb_id)

            if top_k <= 0:
                top_k = kb.top_k if kb else 5
            if score_threshold <= 0:
                score_threshold = kb.score_threshold if kb else 0.5

            knowledge = knowledge_service._get_or_create(kb_id, kb)

        results: list[dict] = []

        try:
            if hasattr(knowledge, "retrieve"):
                raw_results = await knowledge.retrieve(
                    query=query,
                    top_k=top_k,
                    score_threshold=score_threshold,
                )
                for item in raw_results:
                    if isinstance(item, dict):
                        results.append({
                            "content": item.get("content", ""),
                            "source": item.get("source", item.get("metadata", {}).get("source", "")),
                            "page": item.get("page", item.get("metadata", {}).get("page", 0)),
                            "score": item.get("score", 0.0),
                            "chunk_id": item.get("chunk_id", item.get("id", "")),
                        })
                    else:
                        results.append({
                            "content": getattr(item, "content", ""),
                            "source": getattr(item, "source", ""),
                            "page": getattr(item, "page", 0),
                            "score": getattr(item, "score", 0.0),
                            "chunk_id": getattr(item, "chunk_id", getattr(item, "id", "")),
                        })
            elif hasattr(knowledge, "search"):
                raw_results = await knowledge.search(
                    query=query,
                    top_k=top_k,
                )
                for item in raw_results:
                    if isinstance(item, dict):
                        score = item.get("score", 0.0)
                        if score >= score_threshold:
                            results.append({
                                "content": item.get("content", ""),
                                "source": item.get("source", item.get("metadata", {}).get("source", "")),
                                "page": item.get("page", item.get("metadata", {}).get("page", 0)),
                                "score": score,
                                "chunk_id": item.get("chunk_id", item.get("id", "")),
                            })
                    else:
                        score = getattr(item, "score", 0.0)
                        if score >= score_threshold:
                            results.append({
                                "content": getattr(item, "content", ""),
                                "source": getattr(item, "source", ""),
                                "page": getattr(item, "page", 0),
                                "score": score,
                                "chunk_id": getattr(item, "chunk_id", getattr(item, "id", "")),
                            })
            elif hasattr(knowledge, "store") and hasattr(knowledge.store, "search"):
                embedding_model = knowledge.embedding_model
                query_vector = None
                if hasattr(embedding_model, "embed"):
                    vectors = await embedding_model.embed([query])
                    query_vector = vectors[0] if vectors else None
                elif hasattr(embedding_model, "encode"):
                    vectors = embedding_model.encode([query])
                    query_vector = vectors[0] if vectors else None

                if query_vector is not None:
                    search_results = await knowledge.store.search(
                        vector=query_vector,
                        top_k=top_k,
                    )
                    for item in search_results:
                        if isinstance(item, dict):
                            score = item.get("score", 0.0)
                            if score >= score_threshold:
                                payload = item.get("payload", {})
                                results.append({
                                    "content": payload.get("content", ""),
                                    "source": payload.get("source", ""),
                                    "page": payload.get("page", 0),
                                    "score": score,
                                    "chunk_id": item.get("id", ""),
                                })
                        else:
                            score = getattr(item, "score", 0.0)
                            if score >= score_threshold:
                                payload = getattr(item, "payload", {})
                                results.append({
                                    "content": payload.get("content", "") if isinstance(payload, dict) else "",
                                    "source": payload.get("source", "") if isinstance(payload, dict) else "",
                                    "page": payload.get("page", 0) if isinstance(payload, dict) else 0,
                                    "score": score,
                                    "chunk_id": getattr(item, "id", ""),
                                })

        except Exception as e:
            logger.error("Knowledge retrieval failed for kb %s: %s", kb_id, e)

        return results

    except Exception as e:
        logger.error("Retrieve setup failed for kb %s: %s", kb_id, e)
        return []
