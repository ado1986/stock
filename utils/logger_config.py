import logging.config
import os

def setup_logging():
    """设置日志配置"""
    log_dir = './logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'standard',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'standard',
                'filename': os.path.join(log_dir, 'app.log'),
                'maxBytes': 10*1024*1024,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
        },
        'loggers': {
            '': {
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
            },
        },
    }
    
    logging.config.dictConfig(logging_config)