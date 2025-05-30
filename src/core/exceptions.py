"""
自定义异常类
定义项目中使用的各种异常类型
"""


class NewsAgentException(Exception):
    """新闻智能体基础异常"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class DataSourceException(NewsAgentException):
    """数据源相关异常"""
    pass


class APIRateLimitException(DataSourceException):
    """API频率限制异常"""
    pass


class APIAuthenticationException(DataSourceException):
    """API认证异常"""
    pass


class DataQualityException(NewsAgentException):
    """数据质量异常"""
    pass


class ProcessingException(NewsAgentException):
    """内容处理异常"""
    pass


class LLMException(ProcessingException):
    """LLM服务异常"""
    pass


class VectorStoreException(NewsAgentException):
    """向量存储异常"""
    pass


class DatabaseException(NewsAgentException):
    """数据库异常"""
    pass


class ConfigurationException(NewsAgentException):
    """配置异常"""
    pass


class AgentException(NewsAgentException):
    """智能体异常"""
    pass


class ScoringException(NewsAgentException):
    """评分系统异常"""
    pass


class DeliveryException(NewsAgentException):
    """内容交付异常"""
    pass


class SchedulingException(NewsAgentException):
    """调度异常"""
    pass
