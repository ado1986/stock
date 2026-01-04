"""
告警管理模块
负责基于 `stock_concern` 的阈值判断，结合 `stock_price_history` 的最新价格进行告警，
并把告警记录写入 `stock_alert_state` 与 `stock_alert_history` 表，同时通过 NotificationManager 发送通知。
"""
import datetime
import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)


class AlertManager:
    def __init__(self, storage):
        """storage 需实现 get_latest_price, get_alert_state, upsert_alert_state, save_alert_history 等方法"""
        self.storage = storage
        self.cooldown_minutes = int(getattr(settings, "ALERT_COOLDOWN_MINUTES", 60))

    def handle_stock_price_update(self, stock: dict, price: float, time_str: Optional[str] = None):
        """处理单只股票的价格更新并判断是否需要发送告警"""
        try:
            concern_id = stock.get('id')
            stock_code = stock.get('stock_code')
            if concern_id is None or stock_code is None:
                logger.warning("股票信息缺少 id 或 stock_code，无法处理告警")
                return

            # 处理低阈值（price_low）
            price_low = stock.get('price_low')
            if price_low is not None:
                try:
                    low_thr = float(price_low)
                except Exception:
                    low_thr = None

                if low_thr is not None:
                    if price <= low_thr:
                        self._trigger_alert(concern_id, stock_code, 'low', low_thr, price, time_str)
                    else:
                        self._resolve_alert_if_needed(concern_id, stock_code, 'low')

            # 处理高阈值（price_high）
            price_high = stock.get('price_high')
            if price_high is not None:
                try:
                    high_thr = float(price_high)
                except Exception:
                    high_thr = None

                if high_thr is not None:
                    if price >= high_thr:
                        self._trigger_alert(concern_id, stock_code, 'high', high_thr, price, time_str)
                    else:
                        self._resolve_alert_if_needed(concern_id, stock_code, 'high')

        except Exception as e:
            logger.error(f"处理股票告警时报错: {e}")

    def _trigger_alert(self, concern_id, stock_code, alert_type, threshold, price, time_str=None):
        """触发告警（考虑冷却期），发送通知并记录状态/历史"""
        try:
            state = self.storage.get_alert_state(concern_id, alert_type)
            now = datetime.datetime.now()

            # 冷却期判断
            if state and int(state.get('is_triggered', 0)) == 1 and state.get('last_triggered_at'):
                last = state.get('last_triggered_at')
                if isinstance(last, str):
                    try:
                        last_dt = datetime.datetime.strptime(last, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        last_dt = None
                elif isinstance(last, datetime.datetime):
                    last_dt = last
                else:
                    last_dt = None

                if last_dt:
                    elapsed = (now - last_dt).total_seconds()
                    if elapsed < self.cooldown_minutes * 60:
                        logger.info(f"告警 {stock_code} {alert_type} 在冷却期内（{elapsed}s），跳过发送")
                        return

            # 发送通知
            title = f"股票价格告警 - {stock_code}"
            content = f"股票 {stock_code} 当前价格 {price} 触发告警 {alert_type}（阈值 {threshold}），时间: {time_str}"

            notified = False
            error_message = None
            try:
                # 动态从 package 层获取 send_notification（便于在测试中 patch apps.core.alerting.send_notification）
                from apps.core.alerting import send_notification as package_send
                notified = package_send(title, content)
            except Exception as e:
                notified = False
                error_message = str(e)

            # 保存历史
            try:
                self.storage.save_alert_history(concern_id, stock_code, alert_type, threshold, price, 1 if notified else 0, error_message)
            except Exception as e:
                logger.error(f"保存告警历史失败: {e}")

            # 更新告警状态（置为已触发）
            try:
                last_triggered_at = now.strftime("%Y-%m-%d %H:%M:%S")
                self.storage.upsert_alert_state(concern_id, stock_code, alert_type, threshold, 1, last_triggered_at)
            except Exception as e:
                logger.error(f"更新告警状态失败: {e}")

        except Exception as e:
            logger.error(f"触发告警失败: {e}")

    def _resolve_alert_if_needed(self, concern_id, stock_code, alert_type):
        """当价格回到阈值范围时，清除触发状态（如果存在）"""
        try:
            state = self.storage.get_alert_state(concern_id, alert_type)
            if state and int(state.get('is_triggered', 0)) == 1:
                try:
                    self.storage.upsert_alert_state(concern_id, stock_code, alert_type, state.get('threshold') or 0, 0, None)
                    logger.info(f"告警状态已清除: {stock_code} {alert_type}")
                except Exception as e:
                    logger.error(f"清除告警状态失败: {e}")
        except Exception as e:
            logger.error(f"检测并清除告警状态失败: {e}")
