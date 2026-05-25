import re
from pathlib import Path
from typing import Any

from ms3.database.redis_connection import get_redis

_skills_registry: dict[str, dict] = {}


def scan_skill_directory(directory: str) -> list[dict]:
    results = []
    dir_path = Path(directory)
    if not dir_path.exists():
        return results

    for skill_file in dir_path.rglob("SKILL.md"):
        try:
            skill_meta = _parse_skill_md(str(skill_file))
            if skill_meta:
                skill_meta["path"] = str(skill_file)
                skill_meta["directory"] = str(skill_file.parent)
                results.append(skill_meta)
        except Exception:
            continue

    return results


def _parse_skill_md(file_path: str) -> dict | None:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    meta: dict[str, Any] = {"content": content}

    name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if name_match:
        meta["name"] = name_match.group(1).strip()
    else:
        meta["name"] = Path(file_path).parent.name

    desc_match = re.search(r"(?:^|\n)##\s+Description\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if desc_match:
        meta["description"] = desc_match.group(1).strip()
    else:
        meta["description"] = ""

    version_match = re.search(r"(?:^|\n)##\s+Version\s*\n\s*(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if version_match:
        meta["version"] = version_match.group(1).strip()
    else:
        meta["version"] = "1.0.0"

    tools_match = re.search(r"(?:^|\n)##\s+Tools\s*\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if tools_match:
        tools_text = tools_match.group(1).strip()
        tool_names = re.findall(r"[-*]\s+`?(\w+)`?", tools_text)
        meta["tools"] = tool_names
    else:
        meta["tools"] = []

    instructions_match = re.search(r"(?:^|\n)##\s+Instructions\s*\n(.+?)(?=\n##|\Z)", content, re.DOTALL)
    if instructions_match:
        meta["instructions"] = instructions_match.group(1).strip()
    else:
        meta["instructions"] = ""

    return meta


def load_skill(skill_path: str) -> dict:
    path = Path(skill_path)

    if path.is_dir():
        skill_file = path / "SKILL.md"
    elif path.name == "SKILL.md":
        skill_file = path
    else:
        skill_file = path

    if not skill_file.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_file}")

    meta = _parse_skill_md(str(skill_file))
    if meta is None:
        raise ValueError(f"Failed to parse skill: {skill_file}")

    meta["path"] = str(skill_file)
    meta["directory"] = str(skill_file.parent)

    return meta


async def register_skill_to_toolkit(skill_path: str, toolkit: Any) -> None:
    skill = load_skill(skill_path)
    skill_dir = skill.get("directory", "")

    if not skill_dir:
        raise ValueError(f"Cannot determine skill directory from path: {skill_path}")

    try:
        toolkit.register_agent_skill(skill_dir)
    except AttributeError:
        try:
            from agentscope.tool import Toolkit

            if isinstance(toolkit, Toolkit):
                toolkit.register_agent_skill(skill_dir)
            else:
                raise
        except (ImportError, AttributeError):
            pass

    skill_name = skill.get("name", Path(skill_dir).name)
    _skills_registry[skill_name] = skill

    redis = get_redis()
    await redis.hset(
        "skills:registry",
        skill_name,
        f"{skill_dir}|{skill.get('version', '1.0.0')}",
    )


async def list_registered_skills() -> list[dict]:
    redis = get_redis()
    registry = await redis.hgetall("skills:registry")
    results = []

    for name, data in registry.items():
        parts = data.split("|")
        skill_dir = parts[0]
        version = parts[1] if len(parts) > 1 else "1.0.0"

        skill_info: dict[str, Any] = {
            "name": name,
            "directory": skill_dir,
            "version": version,
        }

        cached = _skills_registry.get(name)
        if cached:
            skill_info["description"] = cached.get("description", "")
            skill_info["tools"] = cached.get("tools", [])
            skill_info["instructions"] = cached.get("instructions", "")
        else:
            skill_file = Path(skill_dir) / "SKILL.md"
            if skill_file.exists():
                try:
                    meta = _parse_skill_md(str(skill_file))
                    if meta:
                        skill_info["description"] = meta.get("description", "")
                        skill_info["tools"] = meta.get("tools", [])
                        skill_info["instructions"] = meta.get("instructions", "")
                except Exception:
                    pass

        results.append(skill_info)

    return results


async def get_skill_detail(name: str) -> dict:
    cached = _skills_registry.get(name)
    if cached:
        return cached

    redis = get_redis()
    data = await redis.hget("skills:registry", name)
    if data is None:
        from ms3.common.exceptions import NotFoundException
        raise NotFoundException(f"Skill not found: {name}")

    parts = data.split("|")
    skill_dir = parts[0]

    skill_file = Path(skill_dir) / "SKILL.md"
    if skill_file.exists():
        return load_skill(str(skill_file))

    return {"name": name, "directory": skill_dir}


async def unregister_skill(name: str) -> None:
    _skills_registry.pop(name, None)
    redis = get_redis()
    await redis.hdel("skills:registry", name)
