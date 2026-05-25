import asyncio

from ms3.database.connection import async_session_factory
from ms3.database.dal import ToolDefinitionDAL, ToolGroupDefinitionDAL

PLATFORM_TENANT_ID = "platform"

DOC_TOOLS = [
    {
        "tool_code": "generate_official_document",
        "tool_name": "生成公文",
        "description": "生成公文预览，支持通知/请示/批复/函/决定/意见等公文类型",
        "runtime_type": "function",
        "entrypoint": "ms3.runtime.tools.doc_tools.generate_official_document",
        "schema_json": {
            "type": "object",
            "properties": {
                "doc_type": {
                    "type": "string",
                    "description": "Document type (通知/请示/批复/函/决定/意见)",
                },
                "title": {"type": "string", "description": "Document title"},
                "issuer": {"type": "string", "description": "Document issuer"},
                "recipient": {"type": "string", "description": "Document recipient"},
                "body_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key points for the document body",
                },
            },
            "required": ["doc_type", "title", "issuer", "recipient", "body_points"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 1,
        "permission_behavior": "allow",
    },
    {
        "tool_code": "preview_official_document",
        "tool_name": "预览公文",
        "description": "预览公文格式化排版效果",
        "runtime_type": "function",
        "entrypoint": "ms3.runtime.tools.doc_tools.preview_official_document",
        "schema_json": {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "description": "Document type"},
                "title": {"type": "string", "description": "Document title"},
                "issuer": {"type": "string", "description": "Document issuer"},
                "recipient": {"type": "string", "description": "Document recipient"},
                "body_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key points for the document body",
                },
            },
            "required": ["doc_type", "title", "issuer", "recipient", "body_points"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 1,
        "permission_behavior": "allow",
    },
    {
        "tool_code": "download_official_document",
        "tool_name": "下载公文",
        "description": "生成并下载 Word 格式公文",
        "runtime_type": "function",
        "entrypoint": "ms3.runtime.tools.doc_tools.download_official_document",
        "schema_json": {
            "type": "object",
            "properties": {
                "doc_type": {"type": "string", "description": "Document type"},
                "title": {"type": "string", "description": "Document title"},
                "issuer": {"type": "string", "description": "Document issuer"},
                "recipient": {"type": "string", "description": "Document recipient"},
                "body_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Key points for the document body",
                },
                "date": {"type": "string", "description": "Document date (YYYY-MM-DD)"},
            },
            "required": ["doc_type", "title", "issuer", "recipient", "body_points"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 0,
        "permission_behavior": "allow",
    },
]

STANDALONE_TOOLS = [
    {
        "tool_code": "document_summary",
        "tool_name": "文档摘要",
        "description": "对文档内容进行摘要，支持简要和详细两种模式",
        "runtime_type": "function",
        "entrypoint": "ms3.runtime.tools.summary_tool.document_summary",
        "schema_json": {
            "type": "object",
            "properties": {
                "document_text": {"type": "string", "description": "The document text to summarize"},
                "summary_type": {
                    "type": "string",
                    "description": "Summary type - brief or detailed",
                    "default": "brief",
                },
            },
            "required": ["document_text"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 1,
        "permission_behavior": "allow",
    },
    {
        "tool_code": "email_helper",
        "tool_name": "邮件助手",
        "description": "发送邮件，支持抄送和优先级设置",
        "runtime_type": "function",
        "entrypoint": "ms3.runtime.tools.email_tool.email_helper",
        "schema_json": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string", "description": "Email subject"},
                "body": {"type": "string", "description": "Email body content"},
                "cc": {"type": "string", "description": "CC email address (optional)"},
                "priority": {
                    "type": "string",
                    "description": "Email priority (low/normal/high)",
                    "default": "normal",
                },
            },
            "required": ["to", "subject", "body"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 0,
        "permission_behavior": "allow",
    },
    {
        "tool_code": "image_generator",
        "tool_name": "图片生成",
        "description": "根据文本描述生成图片，异步执行",
        "runtime_type": "external",
        "entrypoint": "ms3.runtime.tools.image_gen_tool.ImageGeneratorTool",
        "schema_json": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Image generation prompt"},
                "size": {
                    "type": "string",
                    "description": "Image size (512x512/1024x1024)",
                    "default": "1024x1024",
                },
                "style": {
                    "type": "string",
                    "description": "Image style (natural/vivid)",
                    "default": "vivid",
                },
            },
            "required": ["prompt"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 0,
        "permission_behavior": "allow",
    },
    {
        "tool_code": "audio_transcription",
        "tool_name": "音频转录",
        "description": "将音频文件转录为文本，异步执行",
        "runtime_type": "external",
        "entrypoint": "ms3.runtime.tools.audio_tool.AudioTranscriptionTool",
        "schema_json": {
            "type": "object",
            "properties": {
                "audio_url": {
                    "type": "string",
                    "description": "URL of the audio file to transcribe",
                },
                "language": {
                    "type": "string",
                    "description": "Audio language (zh/en)",
                    "default": "zh",
                },
            },
            "required": ["audio_url"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 1,
        "permission_behavior": "allow",
    },
    {
        "tool_code": "retrieve_knowledge",
        "tool_name": "知识检索",
        "description": "检索企业知识库中的相关信息。当需要查找企业内部信息时使用此工具。",
        "runtime_type": "function",
        "entrypoint": "ms3.runtime.tools.knowledge_tool.retrieve_knowledge",
        "schema_json": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query for knowledge retrieval"},
                "kb_id": {
                    "type": "string",
                    "description": "Knowledge base ID (optional, uses default if not specified)",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        "is_concurrency_safe": 1,
        "is_read_only": 1,
        "permission_behavior": "allow",
    },
]


async def seed() -> None:
    async with async_session_factory() as session:
        group_dal = ToolGroupDefinitionDAL(session, tenant_id=PLATFORM_TENANT_ID)
        tool_dal = ToolDefinitionDAL(session, tenant_id=PLATFORM_TENANT_ID)

        existing_group = await group_dal.get_by_code("doc-tools")
        if existing_group:
            print(f"[skip] tool group 'doc-tools' already exists (id={existing_group.id})")
            group_id = existing_group.id
        else:
            group = await group_dal.create(
                group_code="doc-tools",
                group_name="党政机关公文生成工具组",
                description="党政机关公文生成工具组",
                instructions=(
                    "使用 generate_official_document 生成公文预览，"
                    "确认后使用 download_official_document 下载 Word 文件。"
                ),
                is_active=1,
            )
            print(f"[created] tool group 'doc-tools' (id={group.id})")
            group_id = group.id

        for tool_def in DOC_TOOLS:
            existing = await tool_dal.list_all(tool_code=tool_def["tool_code"])
            if existing:
                print(f"[skip] tool '{tool_def['tool_code']}' already exists")
                continue
            tool = await tool_dal.create(
                group_id=group_id,
                tool_code=tool_def["tool_code"],
                tool_name=tool_def["tool_name"],
                description=tool_def["description"],
                runtime_type=tool_def["runtime_type"],
                entrypoint=tool_def["entrypoint"],
                schema_json=tool_def["schema_json"],
                is_concurrency_safe=tool_def["is_concurrency_safe"],
                is_read_only=tool_def["is_read_only"],
                permission_behavior=tool_def["permission_behavior"],
            )
            print(f"[created] tool '{tool_def['tool_code']}' (id={tool.id})")

        for tool_def in STANDALONE_TOOLS:
            existing = await tool_dal.list_all(tool_code=tool_def["tool_code"])
            if existing:
                print(f"[skip] tool '{tool_def['tool_code']}' already exists")
                continue
            tool = await tool_dal.create(
                group_id=None,
                tool_code=tool_def["tool_code"],
                tool_name=tool_def["tool_name"],
                description=tool_def["description"],
                runtime_type=tool_def["runtime_type"],
                entrypoint=tool_def["entrypoint"],
                schema_json=tool_def["schema_json"],
                is_concurrency_safe=tool_def["is_concurrency_safe"],
                is_read_only=tool_def["is_read_only"],
                permission_behavior=tool_def["permission_behavior"],
            )
            print(f"[created] tool '{tool_def['tool_code']}' (id={tool.id})")

        await session.commit()
        print("[done] tool seeding complete")


if __name__ == "__main__":
    asyncio.run(seed())
