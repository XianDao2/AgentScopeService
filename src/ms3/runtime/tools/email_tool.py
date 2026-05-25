from agentscope.message import TextBlock
from agentscope.tool import ToolChunk


async def email_helper(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    priority: str = "normal",
) -> ToolChunk:
    """Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        cc: CC email address (optional)
        priority: Email priority (low/normal/high)
    """
    result = f"邮件已发送\n收件人: {to}\n主题: {subject}\n优先级: {priority}"
    if cc:
        result += f"\n抄送: {cc}"
    return ToolChunk(content=[TextBlock(text=result)])
