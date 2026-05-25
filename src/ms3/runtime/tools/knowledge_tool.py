from agentscope.message import TextBlock
from agentscope.tool import ToolChunk, FunctionTool


async def retrieve_knowledge(query: str, kb_id: str = "", top_k: int = 5) -> ToolChunk:
    """Retrieve knowledge from the enterprise knowledge base.

    Args:
        query: Search query for knowledge retrieval
        kb_id: Knowledge base ID (optional, uses default if not specified)
        top_k: Number of results to return
    """
    from ms3.knowledge.retrieve import retrieve

    results = await retrieve(kb_id=kb_id, query=query, top_k=top_k)
    if not results:
        return ToolChunk(content=[TextBlock(text="未找到相关知识。")])

    context_parts = []
    for i, doc in enumerate(results, 1):
        content = doc.get("content", "")
        source = doc.get("source", "未知来源")
        score = doc.get("score", 0)
        context_parts.append(f"[{i}] {content}（来源: {source}, 置信度: {score:.2f}）")

    return ToolChunk(content=[TextBlock(text="\n\n".join(context_parts))])


knowledge_retrieve_tool = FunctionTool(
    retrieve_knowledge,
    name="retrieve_knowledge",
    description="检索企业知识库中的相关信息。当需要查找企业内部信息时使用此工具。",
)
