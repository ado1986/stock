from typing import Optional, Dict


def fetch_stock_yfinance(code: str) -> Dict[str, Optional[object]]:
    """使用 yfinance 抓取股票信息的简单 demo。

    入参示例：'AAPL', '000858.SZ', '600519.SS', '0700.HK'
    返回字段：`code`, `name`, `price`, `pe_ratio`, `dividend_yield`（百分比）
    """
    try:
        import yfinance as yf
    except Exception:
        raise RuntimeError("请先安装 yfinance：pip install yfinance")

    ticker = yf.Ticker(code)
    print(ticker.info.get("symbol"))

    info = {}
    try:
        info = ticker.info or {}
    except Exception:
        # 某些 yfinance 版本或代码会在 .info 上抛错，忽略
        info = {}

    name = info.get("shortName") or info.get("longName") or info.get("short_name")

    # 价格：优先 regularMarketPrice，再试 previousClose，再用 history
    price = info.get("regularMarketPrice")
    if price is None:
        price = info.get("previousClose")
    if price is None:
        try:
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        except Exception:
            price = None

    pe = info.get("trailingPE") or info.get("forwardPE") or info.get("pe")

    div_yield = info.get("dividendYield")
    if div_yield is not None:
        try:
            div_yield = float(div_yield) * 100
        except Exception:
            div_yield = None
    
    return {
        "code": code,
        "name": name,
        "price": float(price) if price is not None else None,
        "pe_ratio": float(pe) if pe is not None else None,
        "dividend_yield": float(div_yield) if div_yield is not None else None,
    }


# 使用示例
if __name__ == "__main__":
    print(fetch_stock_yfinance("000858.SZ"))