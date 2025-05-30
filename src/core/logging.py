"""
日志配置模块
统一的日志记录配置
"""
import sys
from pathlib import Path
from loguru import logger
from .config import config


def setup_logging():
    """设置应用日志配置"""
    
    # 移除默认的日志处理器
    logger.remove()
    
    # 控制台日志格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 文件日志格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # 控制台日志
    logger.add(
        sys.stdout,
        format=console_format,
        level=config.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # 应用日志文件
    logger.add(
        config.logs_dir / "app.log",
        format=file_format,
        level=config.log_level,
        rotation="100 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 错误日志文件
    logger.add(
        config.logs_dir / "error.log",
        format=file_format,
        level="ERROR",
        rotation="50 MB",
        retention="90 days",
        compression="zip",
        encoding="utf-8"
    )
    
    # 性能日志文件
    logger.add(
        config.logs_dir / "performance.log",
        format=file_format,
        level="INFO",
        rotation="50 MB",
        retention="7 days",
        filter=lambda record: "PERFORMANCE" in record["extra"],
        encoding="utf-8"
    )
    
    # Agent决策日志
    logger.add(
        config.logs_dir / "agent_decisions.log",
        format=file_format,
        level="INFO",
        rotation="50 MB",
        retention="30 days",
        filter=lambda record: "AGENT_DECISION" in record["extra"],
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")


def get_logger(name: str):
    """获取指定名称的logger"""
    return logger.bind(name=name)


# 特定用途的logger
def log_performance(message: str, **kwargs):
    """记录性能日志"""
    logger.bind(PERFORMANCE=True).info(message, **kwargs)


def log_agent_decision(agent_name: str, decision: str, context: dict):
    """记录Agent决策日志"""
    logger.bind(AGENT_DECISION=True).info(
        f"Agent: {agent_name} | Decision: {decision} | Context: {context}"
    )


def log_source_quality(source: str, score: float, details: dict):
    """记录信源质量评分日志"""
    logger.info(
        f"信源质量评分 - Source: {source} | Score: {score:.3f} | Details: {details}"
    )


def log_content_processing(content_id: str, stage: str, status: str, details: dict = None):
    """记录内容处理日志"""
    message = f"内容处理 - ID: {content_id} | Stage: {stage} | Status: {status}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)
