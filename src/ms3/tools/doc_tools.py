import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentSearchResult:
    filename: str
    content: str
    score: float
    metadata: Dict[str, Any]


class DocumentSearchTool:
    """
    文档检索工具，根据关键词在知识库中搜索相关文档
    """
    
    name = "document_search"
    description = "在知识库中搜索相关文档，支持关键词检索"
    
    def __init__(self, kb_service=None):
        self.kb_service = kb_service
    
    async def __call__(
        self,
        query: str,
        kb_id: Optional[str] = None,
        top_k: int = 5,
        score_threshold: float = 0.5,
        tenant_id: Optional[str] = None,
    ) -> List[DocumentSearchResult]:
        """
        执行文档搜索
        """
        logger.info(f"Document search: query={query}, kb_id={kb_id}")
        
        results = []
        
        try:
            if self.kb_service:
                if kb_id:
                    kb_ids = [kb_id]
                else:
                    kb_ids = await self._get_accessible_kbs(tenant_id)
                
                for kid in kb_ids:
                    try:
                        kb_results = await self.kb_service.search(
                            kb_id=kid,
                            query=query,
                            top_k=top_k,
                            score_threshold=score_threshold,
                        )
                        
                        for result in kb_results:
                            results.append(DocumentSearchResult(
                                filename=result.filename,
                                content=result.content,
                                score=result.score,
                                metadata=result.metadata or {},
                            ))
                    except Exception as e:
                        logger.error(f"Error searching KB {kid}: {e}")
            
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]
            
        except Exception as e:
            logger.error(f"Document search error: {e}")
            results = []
        
        return results
    
    async def _get_accessible_kbs(self, tenant_id: Optional[str]) -> List[str]:
        if not tenant_id:
            return []
        return []
