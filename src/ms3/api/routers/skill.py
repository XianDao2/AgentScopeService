from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ms3.auth.dependencies import get_current_user_id, get_current_tenant_id
from ms3.auth.rbac import require_permission
from ms3.runtime.skill_loader import (
    scan_skill_directory,
    register_skill_to_toolkit,
    list_registered_skills,
    get_skill_detail,
    unregister_skill,
)

router = APIRouter(tags=["skills"])


class SkillScanRequest(BaseModel):
    directory: str


class SkillResponse(BaseModel):
    name: str
    directory: str | None = None
    version: str = "1.0.0"
    description: str | None = None
    tools: list[str] | None = None
    instructions: str | None = None


class SkillDetailResponse(BaseModel):
    name: str
    path: str | None = None
    directory: str | None = None
    version: str = "1.0.0"
    description: str | None = None
    tools: list[str] | None = None
    instructions: str | None = None
    content: str | None = None


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("skill:list")),
):
    skills = await list_registered_skills()
    return [
        SkillResponse(
            name=s["name"],
            directory=s.get("directory"),
            version=s.get("version", "1.0.0"),
            description=s.get("description"),
            tools=s.get("tools"),
            instructions=s.get("instructions"),
        )
        for s in skills
    ]


@router.post("/skills/scan", response_model=list[SkillResponse])
async def scan_skills(
    body: SkillScanRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("skill:create")),
):
    discovered = scan_skill_directory(body.directory)
    results = []
    for skill in discovered:
        try:
            await register_skill_to_toolkit(skill["path"], toolkit=None)
            results.append(
                SkillResponse(
                    name=skill.get("name", ""),
                    directory=skill.get("directory"),
                    version=skill.get("version", "1.0.0"),
                    description=skill.get("description"),
                    tools=skill.get("tools"),
                    instructions=skill.get("instructions"),
                )
            )
        except Exception:
            results.append(
                SkillResponse(
                    name=skill.get("name", ""),
                    directory=skill.get("directory"),
                    version=skill.get("version", "1.0.0"),
                    description=skill.get("description"),
                    tools=skill.get("tools"),
                )
            )
    return results


@router.get("/skills/{name}", response_model=SkillDetailResponse)
async def get_skill(
    name: str,
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("skill:read")),
):
    try:
        detail = await get_skill_detail(name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return SkillDetailResponse(
        name=detail.get("name", name),
        path=detail.get("path"),
        directory=detail.get("directory"),
        version=detail.get("version", "1.0.0"),
        description=detail.get("description"),
        tools=detail.get("tools"),
        instructions=detail.get("instructions"),
        content=detail.get("content"),
    )


@router.delete("/skills/{name}", status_code=204)
async def remove_skill(
    name: str,
    _: str = Depends(get_current_user_id),
    __: dict = Depends(require_permission("skill:delete")),
):
    await unregister_skill(name)
