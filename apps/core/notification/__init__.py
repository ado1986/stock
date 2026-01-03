"""
通知模块
统一管理各种通知方式，包括企业微信、邮件等
"""
from typing import Protocol, List
import abc
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import requests
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

class NotificationInterface(Protocol):
    """通知接口协议"""
    
    @abc.abstractmethod
    def send(self, title: str, content: str) -> bool:
        """发送通知"""
        pass


class WeChatWorkNotifier(NotificationInterface):
    """企业微信通知器"""
    
    def __init__(self, corp_id: str, corp_secret: str, agent_id: int):
        self.corp_id = corp_id
        self.corp_secret = corp_secret
        self.agent_id = agent_id
        self.access_token = None
        
    def _get_access_token(self):
        """获取访问令牌"""
        if not self.corp_id or not self.corp_secret:
            logger.error("企业微信配置不完整")
            return None
            
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self.corp_id,
            "corpsecret": self.corp_secret
        }
        
        try:
            response = requests.get(url, params=params)
            result = response.json()
            if result.get("access_token"):
                return result["access_token"]
            else:
                logger.error(f"获取企业微信access_token失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取企业微信access_token异常: {e}")
            return None

    def send(self, title: str, content: str) -> bool:
        """发送企业微信消息"""
        access_token = self._get_access_token()
        if not access_token:
            return False
            
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        
        # 如果配置了接收用户列表，则使用指定用户，否则发送给所有人
        to_user = settings.WECHAT_WORK_NOTIFY_USERIDS
        if not to_user:
            to_user = "@all"
        
        data = {
            "touser": to_user,
            "msgtype": "textcard",
            "agentid": self.agent_id,
            "textcard": {
                "title": title,
                "description": content[:500],  # 限制长度
                "url": "https://stock.example.com",
                "btntxt": "查看"
            }
        }
        
        try:
            response = requests.post(url, json=data)
            result = response.json()
            if result.get("errmsg") == "ok":
                logger.info(f"企业微信消息发送成功: {title}")
                return True
            else:
                logger.error(f"企业微信消息发送失败: {result}")
                return False
        except Exception as e:
            logger.error(f"企业微信消息发送异常: {e}")
            return False


class EmailNotifier(NotificationInterface):
    """邮件通知器"""
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        
    def send(self, title: str, content: str) -> bool:
        """发送邮件"""
        if not self.email or not self.password or not settings.EMAIL_RECIPIENTS_LIST:
            logger.error("邮件配置不完整或没有收件人")
            return False
            
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = ", ".join(settings.EMAIL_RECIPIENTS_LIST)
        msg['Subject'] = title
        
        # 添加邮件正文
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        try:
            # 根据配置确定是否使用SSL
            if settings.EMAIL_USE_SSL.lower() == 'true':
                # 使用SSL连接
                context = ssl.create_default_context()
                
                # 如果配置了跳过SSL验证
                if settings.EMAIL_SKIP_SSL_VERIFICATION.lower() == 'true':
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            else:
                # 使用普通连接，然后启动TLS
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
                
            # 登录并发送邮件
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, settings.EMAIL_RECIPIENTS_LIST, text)
            server.quit()
            
            logger.info(f"邮件发送成功: {title} -> {settings.EMAIL_RECIPIENTS_LIST}")
            return True
        except smtplib.SMTPAuthenticationError:
            logger.error("邮件认证失败，请检查邮箱账号和密码")
            return False
        except smtplib.SMTPRecipientsRefused:
            logger.error("邮件收件人被拒绝")
            return False
        except smtplib.SMTPServerDisconnected:
            logger.error("邮件服务器连接断开")
            return False
        except ssl.SSLError as e:
            logger.error(f"SSL证书验证失败: {e}")
            logger.info("如需跳过SSL验证，请设置 EMAIL_SKIP_SSL_VERIFICATION=true")
            return False
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False


class NotificationManager:
    """通知管理器"""
    
    def __init__(self):
        self.notifiers: List[NotificationInterface] = []
        
        # 根据配置添加通知器
        if settings.WECHAT_WORK_CORP_ID and settings.WECHAT_WORK_CORP_SECRET and settings.WECHAT_WORK_AGENT_ID:
            self.notifiers.append(
                WeChatWorkNotifier(
                    settings.WECHAT_WORK_CORP_ID,
                    settings.WECHAT_WORK_CORP_SECRET,
                    settings.WECHAT_WORK_AGENT_ID
                )
            )
            
        if (settings.EMAIL_SMTP_SERVER and settings.EMAIL_ADDRESS and 
            settings.EMAIL_PASSWORD and settings.EMAIL_RECIPIENTS_LIST):
            self.notifiers.append(
                EmailNotifier(
                    settings.EMAIL_SMTP_SERVER,
                    settings.EMAIL_SMTP_PORT,
                    settings.EMAIL_ADDRESS,
                    settings.EMAIL_PASSWORD
                )
            )
    
    def send_notification(self, title: str, content: str) -> bool:
        """发送通知到所有可用的通知器"""
        success_count = 0
        
        for notifier in self.notifiers:
            try:
                if notifier.send(title, content):
                    success_count += 1
            except Exception as e:
                logger.error(f"通知发送异常: {e}")
        
        # 如果至少有一个通知器发送成功，则认为发送成功
        return success_count > 0


# 全局通知管理器实例
notification_manager = NotificationManager()


def send_notification(title: str, content: str) -> bool:
    """发送通知的便捷方法"""
    return notification_manager.send_notification(title, content)