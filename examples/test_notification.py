#!/usr/bin/env python3
"""
企业微信通知功能测试脚本
用于测试企业微信通知功能是否正常工作
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.notification import get_notification_service


def main():
    print("股票监控系统 - 企业微信通知功能测试")
    print("=" * 50)
    
    notifier = get_notification_service()
    
    if notifier.is_enabled():
        print("✅ 检测到已配置企业微信参数")
        print(f"企业ID: {notifier.corp_id}")
        print(f"应用ID: {notifier.agent_id}")
        
        # 获取用户ID列表
        user_ids_input = input("\n请输入要发送的用户ID（多个用户用逗号分隔）: ").strip()
        if not user_ids_input:
            print("❌ 用户ID不能为空")
            return
        
        # 将输入的用户ID转换为列表
        user_ids = [uid.strip() for uid in user_ids_input.split(',')]
        
        print("正在发送测试消息...")
        
        title = "股票监控系统 - 测试消息"
        content = "这是一条测试消息，表示企业微信通知功能已正确配置。"
        
        success = notifier.send_message(user_ids, title, content)
        
        if success:
            print("\n✅ 测试消息发送成功！")
            print("企业微信通知功能已正确配置，您可以收到企业微信通知。")
        else:
            print("\n❌ 测试消息发送失败！")
            print("请检查您的企业微信配置是否正确。")
    else:
        print("❌ 未检测到完整的企业微信配置")
        print("\n要启用企业微信通知功能，请按以下步骤操作：")
        print("1. 注册企业微信账号")
        print("2. 创建应用并获取以下参数：")
        print("   - 企业ID (CorpID)")
        print("   - 应用的Secret")
        print("   - 应用ID (AgentID)")
        print("3. 在项目根目录的 .env 文件中设置以下环境变量：")
        print("   - WECHAT_WORK_CORP_ID: 您的企业ID")
        print("   - WECHAT_WORK_CORP_SECRET: 您的应用Secret")
        print("   - WECHAT_WORK_AGENT_ID: 您的应用ID")
        print("\n示例 .env 文件内容：")
        print("WECHAT_WORK_CORP_ID=ww123456789abcdef")
        print("WECHAT_WORK_CORP_SECRET=123456789abcdef")
        print("WECHAT_WORK_AGENT_ID=1000002")


if __name__ == "__main__":
    main()