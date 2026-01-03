"""
日志配置模块
统一管理项目日志配置
"""
import logging
import os
from pathlib import Path

def setup_logging():
    """设置日志配置"""
    # 创建logs目录
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log", encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")
    
def get_logger(name):
    """获取指定名称的日志记录器"""
    return logging.getLogger(name)