import requests
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod
from stock_fetcher.config import settings

logger = logging.getLogger(__name__)

class NotificationInterface(ABC):
    """
    通知接口，定义了所有通知器必须实现的方法
    """
    
    @abstractmethod
    def is_enabled(self):
        """
        检查通知是否已启用
        """
        pass
    
    @abstractmethod
    def send_message(self, recipients, title, content, msg_type="text"):
        """
        发送消息
        
        Args:
            recipients (str or list): 接收者
            title (str): 消息标题
            content (str): 消息内容
            msg_type (str): 消息类型
        """
        pass


class WeChatWorkNotification(NotificationInterface):
    """
    企业微信通知服务类
    """
    def __init__(self):
        # 从配置中获取企业微信相关参数
        self.corp_id = getattr(settings, 'WECHAT_WORK_CORP_ID', '')
        self.corp_secret = getattr(settings, 'WECHAT_WORK_CORP_SECRET', '')
        self.agent_id = getattr(settings, 'WECHAT_WORK_AGENT_ID', '')
        self.access_token = None
        self.token_expire_time = None
        
        # 企业微信API基础URL
        self.base_url = "https://qyapi.weixin.qq.com/cgi-bin"
        
    def is_enabled(self):
        """
        检查是否配置了企业微信通知
        """
        return all([
            self.corp_id,
            self.corp_secret,
            self.agent_id
        ])
    
    def _get_access_token(self):
        """
        获取企业微信的access_token
        """
        if self.access_token and self.token_expire_time and self.token_expire_time > datetime.now():
            # 如果token未过期，直接使用
            return self.access_token
        
        try:
            url = f"{self.base_url}/gettoken"
            params = {
                'corpid': self.corp_id,
                'corpsecret': self.corp_secret
            }
            
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('errcode') == 0:
                self.access_token = result['access_token']
                # 设置过期时间（提前5分钟刷新）
                expires_in = result.get('expires_in', 7200)
                self.token_expire_time = datetime.now() + timedelta(seconds=expires_in - 300)
                return self.access_token
            else:
                logger.error(f"获取access_token失败: {result}")
                return None
        except Exception as e:
            logger.error(f"获取access_token时发生异常: {e}")
            return None
    
    def send_message(self, user_ids, title, content, msg_type="text"):
        """
        发送企业微信应用消息
        
        Args:
            user_ids (str or list): 接收消息的用户ID列表，多个用户用'|'分隔或传入列表
            title (str): 消息标题
            content (str): 消息内容
            msg_type (str): 消息类型，支持 'text', 'markdown'
        """
        if not self.is_enabled():
            logger.warning("⚠️ 未完整配置企业微信参数，跳过发送企业微信通知")
            return False
        
        access_token = self._get_access_token()
        if not access_token:
            logger.error("❌ 无法获取access_token，无法发送企业微信通知")
            return False
        
        try:
            url = f"{self.base_url}/message/send?access_token={access_token}"
            
            # 处理user_ids参数
            if isinstance(user_ids, list):
                user_ids_str = '|'.join(user_ids)
            else:
                user_ids_str = user_ids
            
            # 构造消息内容
            if msg_type == "markdown":
                message_data = {
                    "touser": user_ids_str,
                    "msgtype": "markdown",
                    "agentid": self.agent_id,
                    "markdown": {
                        "content": f"**{title}**\n\n{content}"
                    },
                    "safe": 0,
                    "enable_id_trans": 0,
                    "enable_duplicate_check": 0
                }
            else:  # 默认为text类型
                message_data = {
                    "touser": user_ids_str,
                    "msgtype": "text",
                    "agentid": self.agent_id,
                    "text": {
                        "content": f"{title}\n\n{content}"
                    },
                    "safe": 0,
                    "enable_id_trans": 0,
                    "enable_duplicate_check": 0
                }
            
            response = requests.post(url, data=json.dumps(message_data, ensure_ascii=False).encode('utf-8'))
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"✅ 企业微信通知发送成功: {title} -> {user_ids_str}")
                return True
            else:
                logger.error(f"❌ 企业微信通知发送失败: {result.get('errmsg', '未知错误')}")
                return False
        except Exception as e:
            logger.error(f"❌ 发送企业微信通知时发生异常: {e}")
            return False


class EmailNotification(NotificationInterface):
    """
    邮件通知服务类
    """
    def __init__(self):
        # 从配置中获取邮件相关参数
        self.smtp_server = getattr(settings, 'EMAIL_SMTP_SERVER', '')
        self.smtp_port = int(getattr(settings, 'EMAIL_SMTP_PORT', 587))
        self.email_address = getattr(settings, 'EMAIL_ADDRESS', '')
        self.email_password = getattr(settings, 'EMAIL_PASSWORD', '')
        # 是否使用SSL连接
        self.use_ssl = getattr(settings, 'EMAIL_USE_SSL', 'true').lower() == 'true'
        
    def is_enabled(self):
        """
        检查是否配置了邮件通知
        """
        return all([
            self.smtp_server,
            self.email_address,
            self.email_password
        ])
    
    def send_message(self, recipients, title, content, msg_type="html"):
        """
        发送邮件通知
        
        Args:
            recipients (str or list): 接收邮件的邮箱地址，可以是单个邮箱或邮箱列表
            title (str): 邮件标题
            content (str): 邮件内容
            msg_type (str): 邮件类型，支持 'html', 'text'
        """
        if not self.is_enabled():
            logger.warning("⚠️ 未完整配置邮件参数，跳过发送邮件通知")
            return False
        
        try:
            # 处理收件人参数
            if isinstance(recipients, list):
                recipient_list = recipients
                recipient_str = ', '.join(recipients)
            else:
                recipient_list = [recipients]
                recipient_str = recipients
            
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = recipient_str
            msg['Subject'] = title
            
            # 根据类型设置邮件内容
            if msg_type == 'html':
                msg.attach(MIMEText(content, 'html', 'utf-8'))
            else:
                msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            server.login(self.email_address, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_address, recipient_list, text)
            server.quit()
            
            logger.info(f"✅ 邮件通知发送成功: {title} -> {recipient_str}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error(f"❌ 邮件认证失败，请检查邮箱地址和密码/授权码是否正确")
            return False
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"❌ 邮件接收者被拒绝，请检查接收者邮箱地址是否正确: {recipient_str}")
            return False
        except smtplib.SMTPServerDisconnected:
            logger.error(f"❌ SMTP服务器连接意外断开，请检查网络连接或SMTP服务器设置")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP错误: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 发送邮件通知时发生异常: {e}")
            return False


class NotificationManager:
    """
    通知管理器，统一管理各种通知方式
    """
    def __init__(self):
        self.notifications = {
            'wechat': WeChatWorkNotification(),
            'email': EmailNotification()
        }
    
    def send_message(self, title, content, msg_type="text", method='email'):
        """
        发送消息到指定的通知方式
        
        Args:
            title (str): 消息标题
            content (str): 消息内容
            msg_type (str): 消息类型，支持 'text', 'markdown', 'html'
            method (str): 发送方式，支持 'email', 'wechat', 'all'
        """
        if method == 'email':
            notification = self.notifications['email']
            if notification.is_enabled():
                recipients = settings.EMAIL_RECIPIENTS_LIST
                if recipients:
                    return notification.send_message(recipients, title, content, msg_type)
                else:
                    logger.warning("⚠️ 未配置邮件接收者")
                    return False
            else:
                logger.warning("⚠️ 未完整配置邮件参数")
                return False
        elif method == 'wechat':
            notification = self.notifications['wechat']
            if notification.is_enabled():
                recipients = getattr(settings, 'WECHAT_WORK_NOTIFY_USERIDS', '')
                if recipients:
                    # 将字符串转换为列表
                    user_list = [uid.strip() for uid in recipients.split(',')]
                    return notification.send_message(user_list, title, content, msg_type)
                else:
                    logger.warning("⚠️ 未配置企业微信接收者")
                    return False
            else:
                logger.warning("⚠️ 未完整配置企业微信参数")
                return False
        elif method == 'all':
            # 向所有启用的通知方式发送消息
            results = []
            for name, notification in self.notifications.items():
                if notification.is_enabled():
                    if name == 'email':
                        recipients = settings.EMAIL_RECIPIENTS_LIST
                        if recipients:
                            results.append(notification.send_message(recipients, title, content, msg_type))
                    elif name == 'wechat':
                        recipients = getattr(settings, 'WECHAT_WORK_NOTIFY_USERIDS', '')
                        if recipients:
                            user_list = [uid.strip() for uid in recipients.split(',')]
                            results.append(notification.send_message(user_list, title, content, msg_type))
            
            # 如果有任何一个通知发送成功，则返回True
            return any(results)
        else:
            logger.error(f"❌ 未知的通知方式: {method}")
            return False


# 创建全局通知管理器实例
notification_manager = NotificationManager()

def get_notification_service():
    """
    获取通知服务实例
    """
    return notification_manager