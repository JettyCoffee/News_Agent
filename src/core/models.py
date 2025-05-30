"""
数据模型定义
定义项目中使用的核心数据结构
"""
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


class ContentType(str, Enum):
    """内容类型枚举"""
    ACADEMIC_PAPER = "academic_paper"
    BLOG_POST = "blog_post"
    NEWS_ARTICLE = "news_article"
    SOCIAL_POST = "social_post"
    TECHNICAL_REPORT = "technical_report"
    CONFERENCE_PAPER = "conference_paper"


class SourceType(str, Enum):
    """信息源类型枚举"""
    ACADEMIC = "academic"
    INDUSTRY = "industry"
    SOCIAL = "social"
    NEWS = "news"
    BLOG = "blog"


class ProcessingStatus(str, Enum):
    """处理状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class QualityLevel(str, Enum):
    """质量等级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class DataSource(BaseModel):
    """数据源模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    source_type: SourceType
    url: str
    api_endpoint: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    update_frequency: int = Field(description="更新频率(秒)")
    is_active: bool = True
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    last_updated: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentItem(BaseModel):
    """内容项模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    content: str
    summary: Optional[str] = None
    url: str
    content_type: ContentType
    source_id: str
    source_name: str
    
    # 元数据
    authors: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)
    language: str = "en"
    
    # 时间信息
    published_at: datetime
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # 质量和评分
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_level: Optional[QualityLevel] = None
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    importance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # 处理状态
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    
    # 额外信息
    metadata: Dict[str, Any] = Field(default_factory=dict)
    raw_data: Optional[Dict[str, Any]] = None
    
    @validator('quality_level', pre=True, always=True)
    def set_quality_level(cls, v, values):
        if v is None and 'quality_score' in values:
            score = values['quality_score']
            if score >= 0.8:
                return QualityLevel.HIGH
            elif score >= 0.6:
                return QualityLevel.MEDIUM
            elif score >= 0.3:
                return QualityLevel.LOW
            else:
                return QualityLevel.VERY_LOW
        return v


class ProcessedContent(BaseModel):
    """处理后的内容模型"""
    content_id: str
    extracted_entities: List[Dict[str, Any]] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    sentiment_score: Optional[float] = None
    topics: List[Dict[str, float]] = Field(default_factory=list)
    
    # 摘要
    executive_summary: Optional[str] = None
    technical_summary: Optional[str] = None
    key_findings: List[str] = Field(default_factory=list)
    
    # 关系信息
    related_papers: List[str] = Field(default_factory=list)
    cited_works: List[str] = Field(default_factory=list)
    
    # 向量表示
    embedding: Optional[List[float]] = None
    
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    processing_version: str = "1.0"


class SourceQualityMetrics(BaseModel):
    """信源质量指标模型"""
    source_id: str
    authority_score: float = Field(ge=0.0, le=1.0)
    accuracy_score: float = Field(ge=0.0, le=1.0)
    timeliness_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    originality_score: float = Field(ge=0.0, le=1.0)
    
    # 综合评分
    overall_score: float = Field(ge=0.0, le=1.0)
    
    # 统计信息
    total_articles: int = 0
    high_quality_articles: int = 0
    user_feedback_count: int = 0
    average_user_rating: float = Field(default=0.0, ge=0.0, le=5.0)
    
    # 时间信息
    evaluation_date: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """用户画像模型"""
    user_id: str
    interests: List[str] = Field(default_factory=list)
    expertise_level: str = "intermediate"  # beginner, intermediate, expert
    preferred_content_types: List[ContentType] = Field(default_factory=list)
    reading_frequency: str = "daily"  # daily, weekly, custom
    
    # 个性化权重
    topic_weights: Dict[str, float] = Field(default_factory=dict)
    source_preferences: Dict[str, float] = Field(default_factory=dict)
    
    # 反馈历史
    feedback_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RecommendationResult(BaseModel):
    """推荐结果模型"""
    user_id: str
    content_items: List[str] = Field(description="推荐的内容ID列表")
    scores: List[float] = Field(description="每个内容的推荐分数")
    reasons: List[str] = Field(description="推荐理由")
    
    recommendation_type: str = "daily"  # daily, weekly, realtime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


class AgentTask(BaseModel):
    """智能体任务模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    task_type: str
    priority: int = Field(default=1, ge=1, le=10)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    status: ProcessingStatus = ProcessingStatus.PENDING
    assigned_agent: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # 重试机制
    retry_count: int = 0
    max_retries: int = 3
