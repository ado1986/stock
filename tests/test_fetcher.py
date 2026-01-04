from apps.core.stock.fetcher import _extract_number, fetch_stock
from unittest.mock import patch


def test_extract_number_percent_and_units():
    assert _extract_number("12.34%") == 12.34
    assert _extract_number("1,234.56") == 1234.56
    assert _extract_number("1.23倍") == 1.23
    assert _extract_number("约 3.5%") == 3.5


def test_fetch_stock_parses_pe_pb_and_computes_roe():
    # 构造 trading-info-box HTML 和 pankou-fold-box HTML
    trading_html = "<div class='price'>95.5</div><div class='time-text'>2026-01-03 12:00:00</div>"
    pankou_html = (
        "<div class='pankou-item'><div class='key'>市盈率(TTM)</div><div class='value'>12.3456</div></div>"
        "<div class='pankou-item'><div class='key'>市净率</div><div class='value'>1.234</div></div>"
    )

    # 当按 selector 不同返回不同 html
    def fake_fetch(stock_path_code, selector):
        if selector == "div.trading-info-box":
            return trading_html
        if selector == "div.pankou-fold-box":
            return pankou_html
        return None

    with patch('apps.core.stock.fetcher.fetch_stock_by_element_selector', side_effect=fake_fetch):
        res = fetch_stock('AAPL')
        assert res['price'] == '95.5'
        assert res['time'] == '2026-01-03 12:00:00'
        assert res['pe_ttm'] == 12.35  # rounded to two decimals
        assert res['pb'] == 1.23
        # ROE = PB / PE * 100
        expected_roe = round((1.234 / 12.3456) * 100, 2)
        assert res['roe'] == expected_roe