from agentscope.message import TextBlock
from agentscope.tool import ToolChunk


async def document_summary(document_text: str, summary_type: str = "brief") -> ToolChunk:
    """Summarize a document.

    Args:
        document_text: The document text to summarize
        summary_type: Summary type - brief or detailed
    """
    word_count = len(document_text)
    preview = document_text[:200] + "..." if len(document_text) > 200 else document_text
    result = f"文档摘要（{summary_type}）\n原文约 {word_count} 字\n\n预览：{preview}"
    return ToolChunk(content=[TextBlock(text=result)])
