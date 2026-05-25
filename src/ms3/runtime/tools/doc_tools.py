from agentscope.tool import FunctionTool, ToolGroup
from agentscope.message import TextBlock
from agentscope.tool import ToolChunk


async def generate_official_document(
    doc_type: str,
    title: str,
    issuer: str,
    recipient: str,
    body_points: list[str],
) -> ToolChunk:
    """Generate an official document preview.

    Args:
        doc_type: Document type (通知/请示/批复/函/决定/意见)
        title: Document title
        issuer: Document issuer
        recipient: Document recipient
        body_points: Key points for the document body
    """
    preview = f"【{doc_type}】\n{title}\n\n{issuer} → {recipient}\n\n"
    for i, point in enumerate(body_points, 1):
        preview += f"{i}. {point}\n"
    return ToolChunk(content=[TextBlock(text=preview)])


async def preview_official_document(
    doc_type: str,
    title: str,
    issuer: str,
    recipient: str,
    body_points: list[str],
) -> ToolChunk:
    """Preview an official document with formatting.

    Args:
        doc_type: Document type
        title: Document title
        issuer: Document issuer
        recipient: Document recipient
        body_points: Key points for the document body
    """
    formatted = (
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"  {doc_type}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{title}\n\n"
        f"{recipient}：\n\n"
    )
    for i, point in enumerate(body_points, 1):
        formatted += f"  {i}. {point}\n"
    formatted += f"\n\n{issuer}\n{__import__('datetime').date.today()}\n"
    return ToolChunk(content=[TextBlock(text=formatted)])


async def download_official_document(
    doc_type: str,
    title: str,
    issuer: str,
    recipient: str,
    body_points: list[str],
    date: str = "",
) -> ToolChunk:
    """Generate and download Word format official document.

    Args:
        doc_type: Document type
        title: Document title
        issuer: Document issuer
        recipient: Document recipient
        body_points: Key points for the document body
        date: Document date (YYYY-MM-DD)
    """
    import datetime

    if not date:
        date = str(datetime.date.today())
    file_url = f"/api/v2/files/official-doc/{doc_type}/{title}/{date}"
    return ToolChunk(content=[TextBlock(text=f"[下载链接]({file_url})")])


doc_tool_group = ToolGroup(
    name="doc-tools",
    description="党政机关公文生成工具组",
    instructions="使用 generate_official_document 生成公文预览，确认后使用 download_official_document 下载 Word 文件。",
    tools=[
        FunctionTool(generate_official_document),
        FunctionTool(preview_official_document),
        FunctionTool(download_official_document),
    ],
)
