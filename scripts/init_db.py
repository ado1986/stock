"""
数据库初始化脚本
用于创建必要的数据表
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from config.settings import settings
import pymysql
from pymysql.cursors import DictCursor


def main():
    print("开始初始化数据库...")

    schema_path = Path(__file__).resolve().parents[2] / "data" / "database_schema.sql"
    if not schema_path.exists():
        print(f"❌ 找不到 schema 文件: {schema_path}")
        sys.exit(1)

    sql_text = schema_path.read_text(encoding='utf-8')
    # 简单按分号分割语句（适用于当前 schema）
    statements = [s.strip() for s in sql_text.split(';') if s.strip()]

    # 先使用不带 database 的连接执行创建数据库语句（如果数据库不存在）
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        cur = conn.cursor()

        for stmt in statements:
            try:
                cur.execute(stmt)
            except Exception as e:
                # 打印并继续执行剩余语句
                print(f"执行语句失败（将继续）: {e}; 语句: {stmt[:120]}")

        conn.commit()
        cur.close()
        conn.close()

        print("✅ schema 执行完成")

    except Exception as e:
        print(f"❌ 初始化数据库失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()