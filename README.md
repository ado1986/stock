# stock_fetcher

简单的 Python 函数，用于通过 Yahoo Finance 抓取单个股票的基础信息。

安装依赖：

```
pip install -r requirements.txt
```

使用示例：

```
python examples/run.py AAPL
# 或仅打印当前配置（便于调试）
python examples/run.py --show-config
```

配置：请复制并修改根目录下的 `.env.example` 到 `.env`，其中包含数据库与请求超时等配置；模块 `stock_fetcher.config.settings` 提供统一访问。

接口：`fetch_stock(code: str) -> dict`
- 返回字段: `code`, `name`, `price`, `pe_ratio`, `dividend_yield`（百分比）
