import logging
from typing import Any, List

logger = logging.getLogger(__name__)


class KnowledgeInjectionMiddleware:
    def __init__(self, kb_ids: List[str]):
        self.kb_ids = kb_ids
        logger.debug(f"KnowledgeInjectionMiddleware initialized with kb_ids: {kb_ids}")

    async def on_system_prompt(self, agent: Any, system_prompt: str, next_handler: Any) -> Any:
        if not self.kb_ids:
            return await next_handler(agent, system_prompt)

        query = self._extract_query(agent)
        if not query:
            return await next_handler(agent, system_prompt)

        try:
            knowledge_context = await self._retrieve_knowledge(query)
            if knowledge_context:
                enhanced_prompt = self._format_prompt_with_knowledge(system_prompt, knowledge_context)
                logger.debug(f"KnowledgeInjectionMiddleware: Enhanced system prompt with {len(knowledge_context)} knowledge chunks")
                return await next_handler(agent, enhanced_prompt)
        except Exception as e:
            logger.error(f"KnowledgeInjectionMiddleware: Failed to retrieve knowledge - {e}")

        return await next_handler(agent, system_prompt)

    def _extract_query(self, agent: Any) -> str:
        if not hasattr(agent, "memory"):
            return ""

        memory = agent.memory
        if hasattr(memory, "get_messages"):
            messages = memory.get_messages()
            if messages:
                last_user_msg = None
                for msg in reversed(messages):
                    if hasattr(msg, "role") and msg.role == "user":
                        last_user_msg = msg
                        break

                if last_user_msg and hasattr(last_user_msg, "content"):
                    content = last_user_msg.content
                    if isinstance(content, str):
                        return content
                    if hasattr(content, "text"):
                        return content.text

        return ""

    async def _retrieve_knowledge(self, query: str) -> List[dict]:
        knowledge_results = []
        for kb_id in self.kb_ids:
            try:
                results = await self._retrieve_from_kb(kb_id, query)
                knowledge_results.extend(results)
            except Exception as e:
                logger.error(f"KnowledgeInjectionMiddleware: Failed to retrieve from kb {kb_id} - {e}")

        return knowledge_results

    async def _retrieve_from_kb(self, kb_id: str, query: str) -> List[dict]:
        logger.debug(f"KnowledgeInjectionMiddleware: Retrieving from kb {kb_id} for query: {query[:50]}...")
        return []

    def _format_prompt_with_knowledge(self, system_prompt: str, knowledge_context: List[dict]) -> str:
        if not knowledge_context:
            return system_prompt

        context_str = "\n\n## 参考知识\n"
        for i, chunk in enumerate(knowledge_context, 1):
            content = chunk.get("content", "")
            source = chunk.get("source", f"知识库片段 {i}")
            context_str += f"\n### {source}\n{content}\n"

        context_str += "\n请根据以上参考知识回答用户问题。如果参考知识中没有相关信息，请直接回答，不要编造信息。"

        return f"{system_prompt}\n{context_str}"
