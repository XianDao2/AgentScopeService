import importlib

from agentscope.model import (
    ChatModelBase,
    DashScopeChatModel,
    OllamaChatModel,
    OpenAIChatModel,
)
from agentscope.formatter import (
    DashScopeChatFormatter,
    DeepSeekChatFormatter,
    FormatterBase,
    OllamaChatFormatter,
    OpenAIChatFormatter,
)

from ms3.models.chat_model import ChatModel as ChatModelRecord
from ms3.models.chat_model import ChatProvider

_PROVIDER_MAP: dict[str, tuple[type[ChatModelBase], type[FormatterBase]]] = {
    "dashscope": (DashScopeChatModel, DashScopeChatFormatter),
    "openai": (OpenAIChatModel, OpenAIChatFormatter),
    "deepseek": (OpenAIChatModel, DeepSeekChatFormatter),
    "zhipu": (OpenAIChatModel, OpenAIChatFormatter),
    "ollama": (OllamaChatModel, OllamaChatFormatter),
}


async def build_model_and_formatter(
    provider: ChatProvider,
    model_record: ChatModelRecord,
) -> tuple[ChatModelBase, FormatterBase]:
    provider_code = provider.provider_code
    model_cls, formatter_cls = _PROVIDER_MAP.get(
        provider_code,
        (OpenAIChatModel, OpenAIChatFormatter),
    )

    api_key = model_record.api_key or ""
    model_name = model_record.model_code

    if provider_code == "dashscope":
        chat_model = model_cls(
            model_name=model_name,
            api_key=api_key,
        )
    elif provider_code == "ollama":
        base_url = model_record.api_base or provider.api_base or "http://localhost:11434"
        chat_model = model_cls(
            model_name=model_name,
            api_key=api_key or "ollama",
            client_kwargs={"base_url": base_url},
        )
    else:
        base_url = model_record.api_base or provider.api_base or ""
        client_kwargs: dict = {}
        if base_url:
            client_kwargs["base_url"] = base_url
        chat_model = model_cls(
            model_name=model_name,
            api_key=api_key,
            client_kwargs=client_kwargs if client_kwargs else None,
        )

    formatter = formatter_cls()
    return chat_model, formatter


def resolve_entrypoint(entrypoint: str):
    module_path, _, func_name = entrypoint.rpartition(":")
    if not module_path:
        module_path, _, func_name = entrypoint.rpartition(".")
    if not module_path:
        raise ValueError(f"Invalid entrypoint format: {entrypoint}")
    module = importlib.import_module(module_path)
    return getattr(module, func_name)
