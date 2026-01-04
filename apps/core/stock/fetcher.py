# -*- coding: utf-8 -*-
import os
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
from typing import Optional, Dict

# 导入yfinance版本的实现
from .yfinance_fetcher import fetch_stock_yfinance

# 导入日志配置
from config.logging_config import get_logger
logger = get_logger(__name__)

def get_chrome_path():
    """获取Chrome浏览器在macOS上的默认安装路径"""
    possible_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Users/{}/Applications/Google Chrome.app/Contents/MacOS/Google Chrome".format(os.environ.get("USER", "")),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def get_element_without_full_load(url, element_selector, timeout=10):
    """不等待页面完全加载就获取元素"""
    try:
        # 配置Chrome选项
        chrome_options = Options()
        chrome_options.page_load_strategy = 'eager'  # 等待DOM加载完成
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # 初始化WebDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # 访问页面（不会等待全部资源加载）
        driver.get(url)
        
        # 显式等待元素出现
        wait = WebDriverWait(driver, timeout)
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, element_selector))
        )
        
        # 确保元素可见
        wait.until(EC.visibility_of(element))
        
        # 获取元素内容
        element_text = element.text
        element_html = element.get_attribute("outerHTML")
        
        # print(f"成功获取元素，文本内容：{element_text[:100]}...")
        return element_html
        
    except Exception as e:
        print(f"获取元素失败：{e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        if 'driver' in locals():
            driver.quit()

def parse_html(html_content):
    """解析盘口数据的HTML内容"""
    # 创建BeautifulSoup解析对象
    soup = BeautifulSoup(html_content, 'lxml')  # 使用lxml解析器
    
    pankou_data = {}

    # 示例1：获取所有段落文本
    print("=== 所有段落文本 ===")
    pankou_items = soup.find_all('div', class_ = 'pankou-item')
    for item in pankou_items:
        key_div = item.find('div', class_='key')
        if key_div:
            key = key_div.get_text(strip=True)
            value_div = item.find('div', class_='value')
            if value_div:
                value=value_div.get_text(strip=True)
                pankou_data[key] = value
    logger.info(pankou_data)
    
    return pankou_data

def fetch_stock_by_element_selector(stock_path_code: str, element_selector: str):
    """抓取指定元素的股票数据"""
    url = f"https://gushitong.baidu.com/stock/{stock_path_code}"
    
    html_content = get_element_without_full_load(url, element_selector)
    return html_content

def fetch_stock(stock_path_code: str, source: Optional[str] = None):
    """抓取股票盘口数据"""
    from config.settings import settings
    # 使用配置中指定的默认数据源，除非明确指定
    if source is None:
        source = settings.DEFAULT_SOURCE
    
    if source == 'yfinance':
        # 使用yfinance获取数据
        return fetch_stock_yfinance(stock_path_code)
    else:
        # 使用爬虫方式获取数据
        path_code = stock_path_code.lower().replace('.', '-')
        html_content = fetch_stock_by_element_selector(path_code, "div.pankou-fold-box")
        if html_content:
            data = parse_html(html_content)
            return data
        else:
            return None

def _extract_number(value: str):
    """从字符串中提取数字，支持带‘%’或中文单位的字符串，返回 float 或 None。"""
    if value is None:
        return None
    try:
        # 去掉中文、单位、倍、等非数字符号，仅保留数字、点和负号与百分号
        v = value.replace('\u200b', '').strip()
        # 如果包含%，保留百分号以便后续处理
        is_percent = '%' in v
        # 去掉中文和单位标识（例如：倍）以及逗号
        import re
        cleaned = re.sub(r"[^0-9.%\-]", "", v)
        if cleaned == '' or cleaned == '.' or cleaned == '-' or cleaned == '%':
            return None
        if is_percent:
            cleaned = cleaned.replace('%', '')
            return float(cleaned)
        return float(cleaned)
    except Exception:
        return None


def fetch_stock_price(stock_path_code: str):
    """抓取指定股票的当日价格，同时尝试抓取 PE / PB / ROE 等关键指标"""
    element_selector = "div.trading-info-box"
    html_content = fetch_stock_by_element_selector(stock_path_code, element_selector)

    price_data = {}

    if html_content:
        # 创建BeautifulSoup解析对象
        soup = BeautifulSoup(html_content, 'lxml')  # 使用lxml解析器
        price_div = soup.find('div', class_='price')
        if price_div:
            price = price_div.get_text(strip=True)
            price_data['price'] = price
        time_div = soup.find('div', class_='time-text')
        #处理时间字符串
        if time_div:
            time_text = time_div.get_text(strip=True)
            price_data['time'] = parse_time_string(time_text)

    # 额外抓取盘口中 PE / PB / ROE 指标（有时在不同区域）
    try:
        pankou_html = fetch_stock_by_element_selector(stock_path_code, "div.pankou-fold-box")
        if pankou_html:
            pankou = parse_html(pankou_html)
            # 常见键名匹配
            pe_candidates = [k for k in pankou.keys() if '市盈' in k]
            pb_candidates = [k for k in pankou.keys() if '市净' in k]
            roe_candidates = [k for k in pankou.keys() if '净资产收益率' in k or 'ROE' in k or '净利率' in k]

            pe_val = None
            pb_val = None
            roe_val = None

            if pe_candidates:
                pe_val = _extract_number(pankou.get(pe_candidates[0]))
            if pb_candidates:
                pb_val = _extract_number(pankou.get(pb_candidates[0]))
            if roe_candidates:
                roe_val = _extract_number(pankou.get(roe_candidates[0]))

            # 格式化为保留两位小数
            if pe_val is not None:
                price_data['pe_ttm'] = round(pe_val, 2)
            if pb_val is not None:
                price_data['pb'] = round(pb_val, 2)
            if roe_val is not None:
                # ROE 按百分数的分子部分存储，例如 '12.34%' -> 12.34
                price_data['roe'] = round(roe_val, 2)

    except Exception as e:
        logger.warning(f"解析盘口指标失败: {e}")

    logger.info(price_data)
    return price_data if price_data else None

def parse_time_string(time_str):
    """解析时间字符串为datetime对象"""
    today = datetime.datetime.today()  # 修复：使用 datetime.datetime.today()
    
    # 尝试多种时间格式
    formats_to_try = [
        "%Y-%m-%d %H:%M:%S",  # 2026-01-02 14:00:00
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",  # 2026-01-02 (如果输入只有日期)
        "%m-%d %H:%M:%S",    # 12-31 15:00:00 -> 2025-12-31 15:00:00
        "%m-%d %H:%M",
        "%H:%M:%S",
        "%H:%M"
    ]
    
    # 尝试解析各种格式
    for fmt in formats_to_try:
        try:
            parsed_time = datetime.datetime.strptime(time_str, fmt)
            
            # 如果是带有年份的格式，直接返回格式化字符串
            if '%Y' in fmt:
                return parsed_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 如果是月日时间格式（如 "12-31 15:00:00"），加上适当的年份
            elif fmt in ["%m-%d %H:%M:%S", "%m-%d %H:%M"]:
                # 判断是否需要使用下一年的年份（例如12-31 15:00:00 在当前日期是1月2日，应该转换为今年的12-31）
                target_date = datetime.datetime(today.year, parsed_time.month, parsed_time.day, parsed_time.hour, parsed_time.minute, parsed_time.second)
                
                # 如果目标日期晚于当前日期，则使用上一年的日期
                if target_date > today.replace(hour=0, minute=0, second=0):
                    target_date = datetime.datetime(today.year - 1, parsed_time.month, parsed_time.day, parsed_time.hour, parsed_time.minute, parsed_time.second)
                    
                return target_date.strftime("%Y-%m-%d %H:%M:%S")
            
            # 如果是只有时间格式，加上今天的日期
            elif fmt in ["%H:%M:%S", "%H:%M"]:
                parsed_time = datetime.datetime(
                    today.year, 
                    today.month, 
                    today.day, 
                    parsed_time.hour, 
                    parsed_time.minute, 
                    parsed_time.second if fmt == "%H:%M:%S" else 0
                )
                return parsed_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 其他情况直接返回解析结果
            return parsed_time.strftime("%Y-%m-%d %H:%M:%S")
            
        except ValueError:
            continue
    
    # 特殊处理只有月日格式的情况，如 "12-31"
    if len(time_str) == 5 and time_str[2] == '-':
        try:
            month, day = time_str.split('-')
            month = int(month)
            day = int(day)
            
            # 创建当前年份的日期
            target_date = datetime.datetime(today.year, month, day)
            
            # 如果目标日期早于当前日期，则使用下一年的日期
            if target_date < today.replace(hour=0, minute=0, second=0):
                target_date = datetime.datetime(today.year + 1, month, day)
            return target_date.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    
    # 如果所有格式都不匹配，抛出异常
    raise ValueError(f"无法解析时间字符串: {time_str}")