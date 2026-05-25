from agentscope.tool import ToolBase
from agentscope.permission import PermissionContext, PermissionDecision, PermissionBehavior


class ImageGeneratorTool(ToolBase):
    name = "image_generator"
    description = "Generate images from text descriptions. Execution is asynchronous."
    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Image generation prompt"},
            "size": {"type": "string", "description": "Image size (512x512/1024x1024)", "default": "1024x1024"},
            "style": {"type": "string", "description": "Image style (natural/vivid)", "default": "vivid"},
        },
        "required": ["prompt"],
    }
    is_concurrency_safe = True
    is_read_only = False
    is_external_tool = True

    async def check_permissions(self, tool_input: dict, context: PermissionContext) -> PermissionDecision:
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Image generation allowed.")
