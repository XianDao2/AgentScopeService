import logging
from typing import Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SummaryResult:
    original_length: int
    summary: str
    key_points: List[str]
    sentiment: Optional[str] = None


class SummaryTool:
    """
    文档摘要工具，对长文本进行智能摘要
    """
    
    name = "summarize_document"
    description = "对文档内容进行智能摘要，提取关键信息"
    
    def __init__(self, llm_model=None):
        self.llm_model = llm_model
    
    async def __call__(
        self,
        content: str,
        max_length: int = 500,
        language: str = "zh-CN",
        include_key_points: bool = True,
        analyze_sentiment: bool = False,
    ) -> SummaryResult:
        logger.info(f"Summarizing document: length={len(content)}")
        
        original_length = len(content)
        
        if not self.llm_model:
            summary = self._simple_summarize(content, max_length)
            key_points = self._extract_simple_key_points(content) if include_key_points else []
            sentiment = "neutral" if analyze_sentiment else None
        else:
            summary, key_points, sentiment = await self._llm_summarize(
                content, max_length, language, include_key_points, analyze_sentiment
            )
        
        return SummaryResult(
            original_length=original_length,
            summary=summary,
            key_points=key_points,
            sentiment=sentiment,
        )
    
    def _simple_summarize(self, content: str, max_length: int) -> str:
        paragraphs = content.split("\n\n")
        summary_parts = []
        current_length = 0
        
        for para in paragraphs:
            if current_length + len(para) <= max_length:
                summary_parts.append(para)
                current_length += len(para) + 2
            else:
                if para:
                    remaining = max_length - current_length
                    if remaining > 50:
                        summary_parts.append(para[:remaining] + "...")
                break
        
        return "\n\n".join(summary_parts)
    
    def _extract_simple_key_points(self, content: str) -> List[str]:
        key_points = []
        sentences = content.split("。")
        
        if sentences:
            key_points.append(sentences[0].strip() + "。")
        
        important_keywords = ["重要", "关键", "核心", "注意", "必须", "建议"]
        for sentence in sentences[1:10]:
            sentence = sentence.strip()
            if any(kw in sentence for kw in important_keywords):
                key_points.append(sentence + "。")
        
        return key_points[:5]
    
    async def _llm_summarize(
        self,
        content: str,
        max_length: int,
        language: str,
        include_key_points: bool,
        analyze_sentiment: bool,
    ):
        summary = self._simple_summarize(content, max_length)
        key_points = self._extract_simple_key_points(content) if include_key_points else []
        sentiment = "neutral" if analyze_sentiment else None
        return summary, key_points, sentiment
