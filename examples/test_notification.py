#!/usr/bin/env python3
"""
测试通知模块的示例文件
用于演示新的通知方式参数（支持 email、wechat、all）
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.notification import get_notification_service


def test_send_message():
    """测试发送消息"""
    notification_service = get_notification_service()
    
    print("开始测试通知功能...")
    print("=" * 50)

    # 检查各种通知方式是否已配置
    email_enabled = notification_service.notifications['email'].is_enabled()

    if email_enabled:
        print("✅ 检测到邮件配置可用")
    else:
        print("⚠️ 未检测到邮件配置，邮件通知将被跳过")

    # 测试使用邮件发送消息
    if email_enabled:
        print("\n测试使用邮件发送消息:")
        result = notification_service.send_message(
            "邮件通知测试", 
            "这是一条通过邮件发送的通知内容。",
            method='email'
        )
        
        if result:
            print("✅ 邮件通知发送成功！")
        else:
            print("❌ 邮件通知发送失败，请检查邮件配置。")
    else:
        print("\n跳过邮件测试 - 未配置SMTP参数")


if __name__ == "__main__":
    test_send_message()