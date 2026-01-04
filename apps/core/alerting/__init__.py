"""告警模块包

将 `AlertManager` 暴露在 `apps.core.alerting` 模块级别以保持向后兼容。
"""

from .manager import AlertManager
from apps.core.notification import send_notification

__all__ = ["AlertManager", "send_notification"]
