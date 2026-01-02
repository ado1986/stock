import requests
import json
import logging
from datetime import datetime, timedelta
from stock_fetcher.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """
    通知服务类，使用企业微信应用消息API发送通知
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

    def send_stock_alert(self, user_ids, stock_name, stock_code, current_price, alert_type, threshold):
        """
        发送股票价格提醒
        
        Args:
            user_ids (str or list): 接收消息的用户ID列表
            stock_name (str): 股票名称
            stock_code (str): 股票代码
            current_price (float): 当前价格
            alert_type (str): 提醒类型 ('low' 或 'high')
            threshold (float): 阈值
        """
        if alert_type == 'low':
            title = f"📉 股价下跌提醒"
            content = f"股票 {stock_name}({stock_code}) 价格已跌至 {current_price} 元，低于设定阈值 {threshold} 元"
        elif alert_type == 'high':
            title = f"📈 股价上涨提醒"
            content = f"股票 {stock_name}({stock_code}) 价格已涨至 {current_price} 元，高于设定阈值 {threshold} 元"
        else:
            logger.error(f"❌ 无效的提醒类型: {alert_type}")
            return False
        
        return self.send_message(user_ids, title, content, msg_type="text")

    def send_operation_notification(self, user_ids, operation, stock_name, stock_code):
        """
        发送操作通知
        
        Args:
            user_ids (str or list): 接收消息的用户ID列表
            operation (str): 操作类型 ('add' 或 'delete')
            stock_name (str): 股票名称
            stock_code (str): 股票代码
        """
        if operation == 'add':
            title = f"✅ 添加股票"
            content = f"已成功添加股票 {stock_name}({stock_code}) 到监控列表"
        elif operation == 'delete':
            title = f"🗑️ 删除股票"
            content = f"已从监控列表中删除股票 {stock_name}({stock_code})"
        else:
            logger.error(f"❌ 无效的操作类型: {operation}")
            return False
        
        return self.send_message(user_ids, title, content, msg_type="text")


# 创建全局通知实例
notification_service = NotificationService()

def get_notification_service():
    """
    获取通知服务实例
    """
    return notification_service