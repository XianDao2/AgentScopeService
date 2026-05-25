import json
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from agentscope.message import Msg

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.common.exceptions import NotFoundException
from ms3.middleware.tenant_context import set_current_tenant_id
from ms3.runtime.agent_builder import PlatformAgentBuilder
from ms3.runtime.state_coordinator import StateCoordinator

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
):
    body = await request.json()
    agent_id = body.get("agent_id")
    session_id = body.get("session_id")
    input_content = body.get("input", {})

    if not agent_id:
        return {"error": "agent_id is required", "code": 400}

    if not session_id:
        session_id = str(uuid.uuid4())

    set_current_tenant_id(tenant_id)

    try:
        builder = PlatformAgentBuilder()
        agent, state = await builder.build_or_restore(
            agent_id=agent_id,
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
    except NotFoundException as e:
        return {"error": str(e), "code": 404}
    except Exception as e:
        return {"error": f"Failed to build agent: {e}", "code": 500}

    content = input_content.get("content", "") if isinstance(input_content, dict) else str(input_content)
    user_msg = Msg(name="user", content=content, role="user")

    async def event_stream():
        try:
            reply_msg = await agent.reply(user_msg)

            event_data = _serialize_reply(reply_msg)
            yield f"data: {json.dumps(event_data, default=str)}\n\n"

            done_event = {"event": "reply_end", "session_id": session_id}
            yield f"data: {json.dumps(done_event)}\n\n"
        except Exception as e:
            error_event = {
                "event": "error",
                "error": str(e),
                "session_id": session_id,
            }
            yield f"data: {json.dumps(error_event)}\n\n"
        finally:
            try:
                coordinator = StateCoordinator()
                await coordinator.persist(
                    agent=agent,
                    agent_id=agent_id,
                    session_id=session_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                )
            except Exception:
                pass

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _serialize_reply(msg: Msg) -> dict:
    content = msg.content
    if isinstance(content, list):
        text_parts = []
        tool_calls = []
        tool_results = []
        for block in content:
            block_type = type(block).__name__
            if block_type == "TextBlock":
                text_parts.append({"type": "text", "text": block.text})
            elif block_type == "ToolUseBlock":
                tool_calls.append({
                    "type": "tool_use",
                    "id": getattr(block, "id", ""),
                    "name": getattr(block, "name", ""),
                    "input": getattr(block, "input", {}),
                })
            elif block_type == "ToolResultBlock":
                tool_results.append({
                    "type": "tool_result",
                    "id": getattr(block, "id", ""),
                    "content": getattr(block, "content", ""),
                })
            elif block_type == "ThinkingBlock":
                text_parts.append({
                    "type": "thinking",
                    "text": getattr(block, "thinking", ""),
                })
            else:
                text_parts.append({"type": block_type, "text": str(block)})

        return {
            "event": "reply",
            "role": msg.role,
            "name": msg.name,
            "content": text_parts,
            "tool_calls": tool_calls,
            "tool_results": tool_results,
            "metadata": msg.metadata,
        }

    return {
        "event": "reply",
        "role": msg.role,
        "name": msg.name,
        "content": str(content) if content is not None else "",
        "metadata": msg.metadata,
    }
