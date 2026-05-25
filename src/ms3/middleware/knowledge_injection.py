from agentscope.middleware import MiddlewareBase


class KnowledgeInjectionMiddleware(MiddlewareBase):
    def __init__(self, kb_ids: list[str]):
        self.kb_ids = kb_ids

    async def on_system_prompt(self, agent, system_prompt):
        from ms3.knowledge.retrieve import retrieve

        results = await retrieve(self.kb_ids, system_prompt, top_k=5)
        if not results:
            return system_prompt

        knowledge_text = "\n\n".join(
            f"[{i + 1}] {r['content']}" for i, r in enumerate(results)
        )
        return f"{system_prompt}\n\n---\nRetrieved Knowledge:\n{knowledge_text}"
