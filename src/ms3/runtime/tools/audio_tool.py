from agentscope.tool import ToolBase
from agentscope.permission import PermissionContext, PermissionDecision, PermissionBehavior


class AudioTranscriptionTool(ToolBase):
    name = "audio_transcription"
    description = "Transcribe audio files to text. Execution is asynchronous."
    input_schema = {
        "type": "object",
        "properties": {
            "audio_url": {"type": "string", "description": "URL of the audio file to transcribe"},
            "language": {"type": "string", "description": "Audio language (zh/en)", "default": "zh"},
        },
        "required": ["audio_url"],
    }
    is_concurrency_safe = True
    is_read_only = True
    is_external_tool = True

    async def check_permissions(self, tool_input: dict, context: PermissionContext) -> PermissionDecision:
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Audio transcription allowed.")
