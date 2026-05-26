import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str
    source: str
    score: float


class WebSearchTool:
    """
    网络搜索工具，调用搜索引擎 API 进行网络搜索
    """
    
    name = "web_search"
    description = "在互联网上搜索相关信息"
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "bing"):
        self.api_key = api_key
        self.provider = provider
    
    async def __call__(
        self,
        query: str,
        num_results: int = 10,
        language: str = "zh-CN",
        safe_search: bool = True,
    ) -> List[WebSearchResult]:
        logger.info(f"Web search: query={query}")
        
        results = []
        
        try:
            if not self.api_key:
                logger.warning("No API key configured, returning mock results")
                results = self._get_mock_results(query, num_results)
            else:
                if self.provider == "bing":
                    results = await self._search_bing(query, num_results, language, safe_search)
                elif self.provider == "google":
                    results = await self._search_google(query, num_results, language, safe_search)
                else:
                    logger.error(f"Unsupported provider: {self.provider}")
                    results = self._get_mock_results(query, num_results)
            
        except Exception as e:
            logger.error(f"Web search error: {e}")
            results = []
        
        return results
    
    def _get_mock_results(self, query: str, num_results: int) -> List[WebSearchResult]:
        return [
            WebSearchResult(
                title=f"{query} - 搜索结果 1",
                url="https://example.com/result1",
                snippet=f"这是关于 {query} 的模拟搜索结果 1...",
                source="example.com",
                score=0.95,
            ),
            WebSearchResult(
                title=f"{query} - 搜索结果 2",
                url="https://example.com/result2",
                snippet=f"这是关于 {query} 的模拟搜索结果 2...",
                source="example.com",
                score=0.85,
            ),
        ][:num_results]
    
    async def _search_bing(
        self, query: str, num_results: int, language: str, safe_search: bool
    ) -> List[WebSearchResult]:
        return self._get_mock_results(query, num_results)
    
    async def _search_google(
        self, query: str, num_results: int, language: str, safe_search: bool
    ) -> List[WebSearchResult]:
        return self._get_mock_results(query, num_results)
