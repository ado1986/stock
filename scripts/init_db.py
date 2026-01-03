"""
数据库初始化脚本
用于创建必要的数据表
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.database import init_database

def main():
    print("开始初始化数据库...")
    
    if init_database():
        print("✅ 数据库初始化成功")
    else:
        print("❌ 数据库初始化失败")
        sys.exit(1)

if __name__ == "__main__":
    main()