import importlib
from unittest.mock import MagicMock, patch


def reload_schedule_task():
    import scripts.schedule_task as schedule_task
    importlib.reload(schedule_task)
    return schedule_task


def test_fetch_task_only_fetches_and_saves():
    storage = MagicMock()
    storage.connect.return_value = True
    storage.query_concern_stocks.return_value = [{"id": 1, "stock_code": "AAPL", "stock_url": "http://example.com"}]

    with patch('config.database.get_db_storage', return_value=storage):
        with patch('apps.core.stock.fetcher.fetch_stock_price', return_value={"price": "95.5", "time": "2026-01-03 12:00:00"}):
            schedule_task = reload_schedule_task()
            schedule_task.fetch_task()

            storage.save_stock_price_history.assert_called_once()
            # 确认抓取任务不会触发告警相关写入
            assert not storage.save_alert_history.called
            assert not storage.upsert_alert_state.called


def test_alert_task_invokes_alert_manager():
    storage = MagicMock()
    storage.connect.return_value = True
    storage.query_concern_stocks.return_value = [{"id": 1, "stock_code": "AAPL", "price_low": 120, "price_high": None}]
    storage.get_latest_price.return_value = {"stock_price": "100.0", "stock_time": "2026-01-03 12:00:00"}

    with patch('config.database.get_db_storage', return_value=storage):
        with patch('apps.core.alerting.AlertManager') as MockAlertManager:
            mock_mgr = MockAlertManager.return_value
            schedule_task = reload_schedule_task()
            schedule_task.alert_task()

            mock_mgr.handle_stock_price_update.assert_called_once_with({"id": 1, "stock_code": "AAPL", "price_low": 120, "price_high": None}, 100.0, "2026-01-03 12:00:00")
