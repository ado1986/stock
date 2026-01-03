from unittest.mock import patch, MagicMock
import smtplib

from apps.core.notification import (
    WeChatWorkNotifier,
    EmailNotifier,
    NotificationManager,
    send_notification,
    notification_manager,
    WeChatWorkNotifier as _WeChat,
    EmailNotifier as _Email,
)
from config.settings import settings


def test_wechat_send_success():
    notifier = WeChatWorkNotifier('corp', 'secret', 100)
    with patch('apps.core.notification.requests.get') as mock_get, patch('apps.core.notification.requests.post') as mock_post:
        mock_get.return_value.json.return_value = {'access_token': 'token'}
        mock_post.return_value.json.return_value = {'errmsg': 'ok'}
        assert notifier.send('title', 'content') is True


def test_wechat_send_token_missing():
    notifier = WeChatWorkNotifier('corp', 'secret', 100)
    with patch('apps.core.notification.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {}
        assert notifier.send('t', 'c') is False


def test_wechat_send_post_failure():
    notifier = WeChatWorkNotifier('corp', 'secret', 100)
    with patch('apps.core.notification.requests.get') as mock_get, patch('apps.core.notification.requests.post') as mock_post:
        mock_get.return_value.json.return_value = {'access_token': 'token'}
        mock_post.return_value.json.return_value = {'errmsg': 'error'}
        assert notifier.send('t', 'c') is False


def test_email_send_ssl_success():
    # 保存原始设置并恢复
    orig_recipients = settings.EMAIL_RECIPIENTS
    orig_use_ssl = settings.EMAIL_USE_SSL

    settings.EMAIL_RECIPIENTS = 'a@example.com'
    settings.EMAIL_USE_SSL = 'true'

    notifier = EmailNotifier('smtp.example.com', 465, 'me@example.com', 'pass')
    with patch('apps.core.notification.smtplib.SMTP_SSL') as mock_ssl:
        server = mock_ssl.return_value
        server.login.return_value = None
        server.sendmail.return_value = None
        server.quit.return_value = None
        assert notifier.send('t', 'c') is True

    settings.EMAIL_RECIPIENTS = orig_recipients
    settings.EMAIL_USE_SSL = orig_use_ssl


def test_email_send_non_ssl_success():
    orig_recipients = settings.EMAIL_RECIPIENTS
    orig_use_ssl = settings.EMAIL_USE_SSL

    settings.EMAIL_RECIPIENTS = 'a@example.com'
    settings.EMAIL_USE_SSL = 'false'

    notifier = EmailNotifier('smtp.example.com', 587, 'me@example.com', 'pass')
    with patch('apps.core.notification.smtplib.SMTP') as mock_smtp:
        server = mock_smtp.return_value
        server.starttls.return_value = None
        server.login.return_value = None
        server.sendmail.return_value = None
        server.quit.return_value = None
        assert notifier.send('t', 'c') is True

    settings.EMAIL_RECIPIENTS = orig_recipients
    settings.EMAIL_USE_SSL = orig_use_ssl


def test_email_send_auth_failure():
    orig_recipients = settings.EMAIL_RECIPIENTS
    orig_use_ssl = settings.EMAIL_USE_SSL

    settings.EMAIL_RECIPIENTS = 'a@example.com'
    settings.EMAIL_USE_SSL = 'true'

    notifier = EmailNotifier('smtp.example.com', 465, 'me@example.com', 'pass')
    with patch('apps.core.notification.smtplib.SMTP_SSL') as mock_ssl:
        server = mock_ssl.return_value
        server.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Auth failed')
        assert notifier.send('t', 'c') is False

    settings.EMAIL_RECIPIENTS = orig_recipients
    settings.EMAIL_USE_SSL = orig_use_ssl


def test_notification_manager_send_combines_notifiers():
    mgr = NotificationManager()
    n1 = MagicMock()
    n1.send.return_value = False
    n2 = MagicMock()
    n2.send.return_value = True
    mgr.notifiers = [n1, n2]

    assert mgr.send_notification('t', 'c') is True
    n1.send.assert_called_once_with('t', 'c')
    n2.send.assert_called_once_with('t', 'c')


def test_send_notification_helper_uses_global_manager():
    orig = notification_manager.notifiers
    try:
        notification_manager.notifiers = [
            MagicMock(send=MagicMock(side_effect=Exception('err'))),
            MagicMock(send=MagicMock(return_value=True)),
        ]
        assert send_notification('t', 'c') is True
    finally:
        notification_manager.notifiers = orig


def test_notification_manager_registers_based_on_settings():
    # 暂时修改 settings 并创建新的实例来验证注册逻辑
    orig = (
        settings.WECHAT_WORK_CORP_ID,
        settings.WECHAT_WORK_CORP_SECRET,
        settings.WECHAT_WORK_AGENT_ID,
        settings.EMAIL_SMTP_SERVER,
        settings.EMAIL_ADDRESS,
        settings.EMAIL_PASSWORD,
        settings.EMAIL_RECIPIENTS,
    )

    settings.WECHAT_WORK_CORP_ID = 'cid'
    settings.WECHAT_WORK_CORP_SECRET = 'secret'
    settings.WECHAT_WORK_AGENT_ID = 100
    settings.EMAIL_SMTP_SERVER = 'smtp'
    settings.EMAIL_ADDRESS = 'a@example.com'
    settings.EMAIL_PASSWORD = 'pass'
    settings.EMAIL_RECIPIENTS = 'a@example.com'

    mgr = NotificationManager()
    assert any(hasattr(n, 'send') for n in mgr.notifiers)

    # 恢复原始配置
    (
        settings.WECHAT_WORK_CORP_ID,
        settings.WECHAT_WORK_CORP_SECRET,
        settings.WECHAT_WORK_AGENT_ID,
        settings.EMAIL_SMTP_SERVER,
        settings.EMAIL_ADDRESS,
        settings.EMAIL_PASSWORD,
        settings.EMAIL_RECIPIENTS,
    ) = orig
