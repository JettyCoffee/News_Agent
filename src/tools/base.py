"""
Langchain工具基类
定义项目中使用的各种工具的基类和接口
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from ..core.models import DataSource, ContentItem
from ..core.logging import get_logger
from ..core.exceptions import NewsAgentException


class ToolResult(BaseModel):
    """工具执行结果模型"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: Optional[float] = None


class NewsAgentBaseTool(BaseTool, ABC):
    """新闻智能体基础工具类"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = get_logger(f"tool.{self.__class__.__name__}")
    
    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> ToolResult:
        """运行工具的主要方法"""
        try:
            self.logger.info(f"开始执行工具: {self.name}, 查询: {query}")
            
            # 执行具体的工具逻辑
            result = self._execute(query, run_manager)
            
            self.logger.info(f"工具执行成功: {self.name}")
            return result
            
        except Exception as e:
            self.logger.error(f"工具执行失败: {self.name}, 错误: {str(e)}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool_name": self.name, "query": query}
            )
    
    @abstractmethod
    def _execute(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> ToolResult:
        """子类需要实现的具体执行逻辑"""
        pass


class DataSourceTool(NewsAgentBaseTool):
    """数据源工具基类"""
    
    def __init__(self, source_config: DataSource, **kwargs):
        super().__init__(**kwargs)
        self.source_config = source_config
    
    @abstractmethod
    def fetch_content(self, **kwargs) -> List[ContentItem]:
        """获取内容的抽象方法"""
        pass
    
    @abstractmethod
    def validate_connection(self) -> bool:
        """验证连接的抽象方法"""
        pass


class ProcessingTool(NewsAgentBaseTool):
    """内容处理工具基类"""
    
    @abstractmethod
    def process_content(self, content: ContentItem) -> ContentItem:
        """处理内容的抽象方法"""
        pass


class QualityEvaluationTool(NewsAgentBaseTool):
    """质量评估工具基类"""
    
    @abstractmethod
    def evaluate_content_quality(self, content: ContentItem) -> float:
        """评估内容质量的抽象方法"""
        pass
    
    @abstractmethod
    def evaluate_source_quality(self, source: DataSource, recent_content: List[ContentItem]) -> float:
        """评估信源质量的抽象方法"""
        pass


class StorageTool(NewsAgentBaseTool):
    """存储工具基类"""
    
    @abstractmethod
    def store_content(self, content: ContentItem) -> str:
        """存储内容的抽象方法"""
        pass
    
    @abstractmethod
    def retrieve_content(self, content_id: str) -> Optional[ContentItem]:
        """检索内容的抽象方法"""
        pass
    
    @abstractmethod
    def search_content(self, query: str, **kwargs) -> List[ContentItem]:
        """搜索内容的抽象方法"""
        pass
