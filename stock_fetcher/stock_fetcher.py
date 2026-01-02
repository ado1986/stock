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

logger = logging.getLogger(__name__)

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

def fetch_stock(stock_path_code: str):
    """抓取股票盘口数据"""
    path_code = stock_path_code.lower().replace('.', '-')
    html_content = fetch_stock_by_element_selector(path_code, "div.pankou-fold-box")
    if html_content:
        data = parse_html(html_content)
        return data
    else:
        return None

def fetch_stock_price(stock_path_code: str):
    """抓取指定股票的当日价格"""
    element_selector = "div.trading-info-box"
    html_content = fetch_stock_by_element_selector(stock_path_code, element_selector)
    if html_content:
        # 创建BeautifulSoup解析对象
        soup = BeautifulSoup(html_content, 'lxml')  # 使用lxml解析器
        price_data = {}
        price_div = soup.find('div', class_='price')
        if price_div:
            price = price_div.get_text(strip=True)
            price_data['price'] = price
        time_div = soup.find('div', class_='time-text')
        #处理时间字符串
        if time_div:
            time_text = time_div.get_text(strip=True)
            price_data['time'] = parse_time_string(time_text)
        logger.info(price_data)
        return price_data
    else:
        return None

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

# 使用示例
if __name__ == "__main__":
    fetch_stock_price('ab-601318')
    # # 配置参数
    # target_url = "https://gushitong.baidu.com/stock/ab-000858"  # 测试网址
    # element_selector = "div.pankou-fold-box"  # 简单选择器，确保能找到元素
    
    # print("===== Chrome网页内容获取工具 =====")
    # print(f"目标网址: {target_url}")
    # print(f"元素选择器: {element_selector}")
    # print("=" * 40)
    
    # # 执行获取操作
    # result = get_element_without_full_load(target_url, element_selector)
    
    # if result:
    #     print("\n✅ 获取成功！HTML内容预览:")
    #     #print(result[:500] + "..." if len(result) > 500 else result)
    #     #print(result)
    #     parse_html(result)
    # else:
    #     print("\n❌ 获取失败，请检查错误信息")