import datetime
from unittest.mock import MagicMock, patch

from apps.core.alerting import AlertManager


def test_trigger_alert_when_breach():
    storage = MagicMock()
    storage.get_alert_state.return_value = None
    storage.save_alert_history.return_value = True
    storage.upsert_alert_state.return_value = True

    with patch('apps.core.alerting.send_notification') as mock_send:
        mock_send.return_value = True
        mgr = AlertManager(storage)
        stock = {'id': 1, 'stock_code': 'AAPL', 'price_low': 120, 'price_high': None}
        mgr.handle_stock_price_update(stock, 100.0, '2026-01-03 12:00:00')

        mock_send.assert_called_once()
        storage.upsert_alert_state.assert_called_once()
        storage.save_alert_history.assert_called_once()


def test_do_not_notify_if_in_cooldown():
    storage = MagicMock()
    now = datetime.datetime.now()
    last_triggered = (now - datetime.timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    storage.get_alert_state.return_value = {'id':1,'is_triggered':1,'last_triggered_at': last_triggered}
    storage.save_alert_history.return_value = True
    storage.upsert_alert_state.return_value = True

    with patch('apps.core.alerting.send_notification') as mock_send:
        mgr = AlertManager(storage)
        mgr.cooldown_minutes = 60  # 设置冷却期为 60 分钟
        stock = {'id': 1, 'stock_code': 'AAPL', 'price_low': 120}
        mgr.handle_stock_price_update(stock, 100.0, '2026-01-03 12:00:00')

        mock_send.assert_not_called()