"""
配置管理模块
处理所有环境变量和应用配置
"""
from typing import Optional, List
from pydantic import BaseSettings, validator
import os
from pathlib import Path


class DatabaseConfig(BaseSettings):
    """数据库配置"""
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "news_agent"
    postgres_user: str = "news_agent_user"
    postgres_password: str = ""
    
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    influxdb_url: str = "http://localhost:8086"
    influxdb_token: str = ""
    influxdb_org: str = "news_agent_org"
    influxdb_bucket: str = "news_agent_metrics"

    @property
    def postgres_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_prefix = ""


class LLMConfig(BaseSettings):
    """大语言模型配置"""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "news-agent"
    
    # 默认模型选择
    default_llm_provider: str = "openai"
    default_model: str = "gpt-4"
    fallback_model: str = "gpt-3.5-turbo"
    
    # API调用配置
    max_tokens: int = 4000
    temperature: float = 0.1
    request_timeout: int = 60

    class Config:
        env_prefix = ""


class VectorStoreConfig(BaseSettings):
    """向量存储配置"""
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    default_vector_store: str = "chroma"  # chroma, pinecone, weaviate
    
    # Embedding配置
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_dimension: int = 384
    similarity_threshold: float = 0.7

    class Config:
        env_prefix = ""


class DataSourceConfig(BaseSettings):
    """数据源配置"""
    twitter_bearer_token: str = ""
    linkedin_access_token: str = ""
    
    # 信息源优先级和权重
    source_weights: dict = {
        "arxiv": 0.9,
        "semantic_scholar": 0.85,
        "openai_blog": 0.95,
        "deepmind_blog": 0.95,
        "twitter": 0.6,
        "linkedin": 0.7
    }
    
    # 更新频率配置
    update_intervals: dict = {
        "arxiv": 3600,  # 1小时
        "blogs": 7200,   # 2小时
        "social": 1800   # 30分钟
    }

    class Config:
        env_prefix = ""


class ProcessingConfig(BaseSettings):
    """内容处理配置"""
    max_summary_length: int = 500
    min_content_quality_score: float = 0.7
    default_language: str = "zh-cn"
    
    # 并发处理配置
    max_concurrent_requests: int = 10
    batch_size: int = 20
    
    # 去重和过滤配置
    similarity_threshold: float = 0.85
    min_content_length: int = 100

    class Config:
        env_prefix = ""


class APIConfig(BaseSettings):
    """API服务配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    api_rate_limit: int = 100
    cors_origins: List[str] = ["*"]

    class Config:
        env_prefix = ""


class EmailConfig(BaseSettings):
    """邮件配置"""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_email: str = ""
    from_name: str = "AI News Agent"

    class Config:
        env_prefix = ""


class AppConfig(BaseSettings):
    """主应用配置"""
    debug: bool = False
    log_level: str = "INFO"
    timezone: str = "Asia/Shanghai"
    
    # 组件配置
    database: DatabaseConfig = DatabaseConfig()
    llm: LLMConfig = LLMConfig()
    vector_store: VectorStoreConfig = VectorStoreConfig()
    data_source: DataSourceConfig = DataSourceConfig()
    processing: ProcessingConfig = ProcessingConfig()
    api: APIConfig = APIConfig()
    email: EmailConfig = EmailConfig()
    
    # 项目路径
    project_root: Path = Path(__file__).parent.parent.parent
    data_dir: Path = project_root / "data"
    logs_dir: Path = project_root / "logs"
    config_dir: Path = project_root / "config"

    @validator('log_level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'log_level must be one of {valid_levels}')
        return v.upper()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        self.data_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置实例
config = AppConfig()
