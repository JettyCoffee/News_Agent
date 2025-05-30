"""
ArXiv数据源工具
从ArXiv获取AI/ML相关论文
"""
import arxiv
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from langchain.callbacks.manager import CallbackManagerForToolRun

from .base import DataSourceTool, ToolResult
from ..core.models import ContentItem, ContentType, DataSource
from ..core.exceptions import DataSourceException


class ArxivTool(DataSourceTool):
    """ArXiv论文获取工具"""
    
    name = "arxiv_fetcher"
    description = "从ArXiv获取AI/ML领域的最新论文"
    
    def __init__(self, source_config: DataSource, **kwargs):
        super().__init__(source_config, **kwargs)
        self.client = arxiv.Client()
        
        # ArXiv相关分类
        self.ai_categories = [
            "cs.AI",    # Artificial Intelligence
            "cs.LG",    # Machine Learning  
            "cs.CL",    # Computation and Language
            "cs.CV",    # Computer Vision
            "cs.NE",    # Neural and Evolutionary Computing
            "stat.ML",  # Machine Learning (Statistics)
        ]
    
    def _execute(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> ToolResult:
        """执行ArXiv查询"""
        try:
            # 解析查询参数
            params = self._parse_query(query)
            content_items = self.fetch_content(**params)
            
            return ToolResult(
                success=True,
                data=content_items,
                metadata={
                    "source": "arxiv",
                    "count": len(content_items),
                    "categories": self.ai_categories
                }
            )
        except Exception as e:
            raise DataSourceException(f"ArXiv查询失败: {str(e)}")
    
    def fetch_content(
        self,
        max_results: int = 50,
        days_back: int = 1,
        categories: Optional[List[str]] = None,
        **kwargs
    ) -> List[ContentItem]:
        """从ArXiv获取内容"""
        
        categories = categories or self.ai_categories
        content_items = []
        
        # 构建搜索查询
        category_query = " OR ".join([f"cat:{cat}" for cat in categories])
        
        # 时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            # 执行搜索
            search = arxiv.Search(
                query=category_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            for paper in self.client.results(search):
                # 检查时间范围
                if paper.published < start_date:
                    continue
                
                content_item = self._convert_to_content_item(paper)
                content_items.append(content_item)
                
            self.logger.info(f"从ArXiv获取到 {len(content_items)} 篇论文")
            return content_items
            
        except Exception as e:
            self.logger.error(f"ArXiv内容获取失败: {str(e)}")
            raise DataSourceException(f"ArXiv API错误: {str(e)}")
    
    def _convert_to_content_item(self, paper: arxiv.Result) -> ContentItem:
        """将ArXiv论文转换为ContentItem"""
        
        # 提取作者信息
        authors = [author.name for author in paper.authors]
        
        # 提取分类信息
        categories = [cat.strip() for cat in paper.categories]
        
        # 构建完整内容
        content_parts = [
            f"标题: {paper.title}",
            f"作者: {', '.join(authors)}",
            f"摘要: {paper.summary}",
        ]
        
        if paper.comment:
            content_parts.append(f"备注: {paper.comment}")
        
        full_content = "\n\n".join(content_parts)
        
        return ContentItem(
            title=paper.title,
            content=full_content,
            summary=paper.summary,
            url=paper.pdf_url,
            content_type=ContentType.ACADEMIC_PAPER,
            source_id=self.source_config.id,
            source_name=self.source_config.name,
            authors=authors,
            categories=categories,
            tags=categories,  # 使用分类作为标签
            language="en",
            published_at=paper.published,
            metadata={
                "arxiv_id": paper.get_short_id(),
                "doi": paper.doi,
                "primary_category": paper.primary_category,
                "journal_ref": paper.journal_ref,
                "links": [link.href for link in paper.links],
                "pdf_url": paper.pdf_url,
                "entry_id": paper.entry_id
            },
            raw_data={
                "arxiv_result": {
                    "entry_id": paper.entry_id,
                    "updated": paper.updated.isoformat() if paper.updated else None,
                    "published": paper.published.isoformat(),
                    "title": paper.title,
                    "authors": [{"name": a.name} for a in paper.authors],
                    "summary": paper.summary,
                    "comment": paper.comment,
                    "journal_ref": paper.journal_ref,
                    "doi": paper.doi,
                    "primary_category": paper.primary_category,
                    "categories": paper.categories,
                    "links": [{"href": link.href, "title": link.title} for link in paper.links]
                }
            }
        )
    
    def validate_connection(self) -> bool:
        """验证ArXiv连接"""
        try:
            # 执行一个简单的测试查询
            search = arxiv.Search(
                query="cat:cs.AI",
                max_results=1
            )
            
            results = list(self.client.results(search))
            return len(results) > 0
            
        except Exception as e:
            self.logger.error(f"ArXiv连接验证失败: {str(e)}")
            return False
    
    def _parse_query(self, query: str) -> Dict[str, Any]:
        """解析查询字符串"""
        # 默认参数
        params = {
            "max_results": 50,
            "days_back": 1,
            "categories": None
        }
        
        # 这里可以添加更复杂的查询解析逻辑
        # 例如解析 "max_results:100 days_back:7" 这样的查询
        
        return params
    
    def get_recent_papers(self, hours: int = 24) -> List[ContentItem]:
        """获取最近几小时的论文"""
        return self.fetch_content(
            days_back=max(1, hours // 24),
            max_results=100
        )
    
    def search_papers_by_keyword(self, keywords: List[str], max_results: int = 20) -> List[ContentItem]:
        """根据关键词搜索论文"""
        try:
            # 构建关键词查询
            keyword_query = " AND ".join([f'"{keyword}"' for keyword in keywords])
            
            search = arxiv.Search(
                query=keyword_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            content_items = []
            for paper in self.client.results(search):
                content_item = self._convert_to_content_item(paper)
                content_items.append(content_item)
            
            return content_items
            
        except Exception as e:
            self.logger.error(f"ArXiv关键词搜索失败: {str(e)}")
            raise DataSourceException(f"ArXiv关键词搜索错误: {str(e)}")
