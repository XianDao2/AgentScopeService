import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.ms3.common.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CredentialAdapter:
    """
    将 chat_provider/chat_model 转换为 AgentScope Credential 和 ChatModel
    """

    def __init__(self):
        self._provider_adapters = {
            "dashscope": self._adapt_dashscope,
            "openai": self._adapt_openai,
            "anthropic": self._adapt_anthropic,
            "ollama": self._adapt_ollama,
        }

    async def convert_to_model_config(
        self,
        chat_provider: Any,
        chat_model: Any,
        credential_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        转换为模型配置

        Args:
            chat_provider: 聊天提供商模型
            chat_model: 聊天模型
            credential_id: 可选的凭证 ID

        Returns:
            模型配置字典
        """
        try:
            logger.info(f"Converting model config for: {chat_provider.provider_name}/{chat_model.model_name}")

            provider_type = chat_provider.provider_type.lower()

            # 获取适配函数
            adapter = self._provider_adapters.get(provider_type)
            if not adapter:
                raise ValueError(f"Unsupported provider type: {provider_type}")

            # 执行适配
            model_config = await adapter(chat_provider, chat_model, credential_id)

            logger.info(f"Successfully converted model config for {chat_model.model_name}")
            return model_config

        except Exception as e:
            logger.error(f"Failed to convert model config: {str(e)}")
            raise

    async def _adapt_dashscope(
        self,
        chat_provider: Any,
        chat_model: Any,
        credential_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        适配阿里云百炼 (DashScope)

        Args:
            chat_provider: 提供商配置
            chat_model: 模型配置
            credential_id: 凭证 ID

        Returns:
            模型配置
        """
        api_key = await self._get_api_key(credential_id) or settings.dashscope_api_key

        if not api_key:
            raise ValueError("DashScope API key not configured")

        return {
            "model_type": "dashscope",
            "model_name": chat_model.model_name,
            "api_key": api_key,
            "base_url": chat_provider.base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "generation_config": {
                "temperature": 0.7,
                "max_tokens": chat_model.max_tokens or 2048,
                "top_p": 0.9,
            },
        }

    async def _adapt_openai(
        self,
        chat_provider: Any,
        chat_model: Any,
        credential_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        适配 OpenAI

        Args:
            chat_provider: 提供商配置
            chat_model: 模型配置
            credential_id: 凭证 ID

        Returns:
            模型配置
        """
        api_key = await self._get_api_key(credential_id)

        if not api_key:
            raise ValueError("OpenAI API key not configured")

        return {
            "model_type": "openai",
            "model_name": chat_model.model_name,
            "api_key": api_key,
            "base_url": chat_provider.base_url or "https://api.openai.com/v1",
            "generation_config": {
                "temperature": 0.7,
                "max_tokens": chat_model.max_tokens or 2048,
                "top_p": 0.9,
            },
        }

    async def _adapt_anthropic(
        self,
        chat_provider: Any,
        chat_model: Any,
        credential_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        适配 Anthropic

        Args:
            chat_provider: 提供商配置
            chat_model: 模型配置
            credential_id: 凭证 ID

        Returns:
            模型配置
        """
        api_key = await self._get_api_key(credential_id)

        if not api_key:
            raise ValueError("Anthropic API key not configured")

        return {
            "model_type": "anthropic",
            "model_name": chat_model.model_name,
            "api_key": api_key,
            "base_url": chat_provider.base_url or "https://api.anthropic.com",
            "generation_config": {
                "temperature": 0.7,
                "max_tokens": chat_model.max_tokens or 2048,
                "top_p": 0.9,
            },
        }

    async def _adapt_ollama(
        self,
        chat_provider: Any,
        chat_model: Any,
        credential_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        适配 Ollama

        Args:
            chat_provider: 提供商配置
            chat_model: 模型配置
            credential_id: 凭证 ID

        Returns:
            模型配置
        """
        return {
            "model_type": "ollama",
            "model_name": chat_model.model_name,
            "base_url": chat_provider.base_url or "http://localhost:11434",
            "generation_config": {
                "temperature": 0.7,
                "max_tokens": chat_model.max_tokens or 2048,
                "top_p": 0.9,
            },
        }

    async def _get_api_key(self, credential_id: Optional[str]) -> Optional[str]:
        """
        获取 API Key

        Args:
            credential_id: 凭证 ID

        Returns:
            API Key
        """
        if not credential_id:
            return None

        # TODO: 从数据库查询凭证
        # 这里是一个占位实现
        logger.warning(f"Credential lookup not implemented for id: {credential_id}")
        return None

    def create_credential(
        self,
        model_config: Dict[str, Any],
    ) -> Any:
        """
        创建 AgentScope Credential

        Args:
            model_config: 模型配置

        Returns:
            Credential 实例
        """
        try:
            from agentscope.credential import DashScopeCredential, OpenAICredential, AnthropicCredential

            model_type = model_config.get("model_type")

            if model_type == "dashscope":
                return DashScopeCredential(
                    api_key=model_config["api_key"],
                )
            elif model_type == "openai":
                return OpenAICredential(
                    api_key=model_config["api_key"],
                    base_url=model_config.get("base_url"),
                )
            elif model_type == "anthropic":
                return AnthropicCredential(
                    api_key=model_config["api_key"],
                    base_url=model_config.get("base_url"),
                )
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

        except ImportError:
            logger.warning("AgentScope not available, returning mock credential")
            return model_config

    def create_chat_model(
        self,
        model_config: Dict[str, Any],
        credential: Any = None,
    ) -> Any:
        """
        创建 AgentScope ChatModel

        Args:
            model_config: 模型配置
            credential: 可选的 Credential

        Returns:
            ChatModel 实例
        """
        try:
            from agentscope.model import (
                DashScopeChatModel,
                OpenAIChatModel,
                AnthropicChatModel,
                OllamaChatModel,
            )

            model_type = model_config.get("model_type")

            if model_type == "dashscope":
                return DashScopeChatModel(
                    model_name=model_config["model_name"],
                    api_key=model_config.get("api_key"),
                    base_url=model_config.get("base_url"),
                    generation_config=model_config.get("generation_config", {}),
                )
            elif model_type == "openai":
                return OpenAIChatModel(
                    model_name=model_config["model_name"],
                    api_key=model_config.get("api_key"),
                    base_url=model_config.get("base_url"),
                    generation_config=model_config.get("generation_config", {}),
                )
            elif model_type == "anthropic":
                return AnthropicChatModel(
                    model_name=model_config["model_name"],
                    api_key=model_config.get("api_key"),
                    base_url=model_config.get("base_url"),
                    generation_config=model_config.get("generation_config", {}),
                )
            elif model_type == "ollama":
                return OllamaChatModel(
                    model_name=model_config["model_name"],
                    base_url=model_config.get("base_url"),
                    generation_config=model_config.get("generation_config", {}),
                )
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

        except ImportError:
            logger.warning("AgentScope not available, returning mock chat model")
            return model_config
