# -*- coding: utf-8 -*-
import os
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
        
        print(f"成功获取元素，文本内容：{element_text[:100]}...")
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
    """解析HTML内容并提取数据"""
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

def fetch_stock(stock_url: str):
    """抓取股票盘口数据的示例函数"""
    path_code = stock_url.lower().replace('.', '-')
    url = f"https://gushitong.baidu.com/stock/{path_code}"
    
    element_selector = "div.pankou-fold-box"
    
    html_content = get_element_without_full_load(url, element_selector)
    if html_content:
        data = parse_html(html_content)
        return data
    else:
        return None


# 使用示例
if __name__ == "__main__":
    # 配置参数
    target_url = "https://gushitong.baidu.com/stock/ab-000858"  # 测试网址
    element_selector = "div.pankou-fold-box"  # 简单选择器，确保能找到元素
    
    print("===== Chrome网页内容获取工具 =====")
    print(f"目标网址: {target_url}")
    print(f"元素选择器: {element_selector}")
    print("=" * 40)
    
    # 执行获取操作
    result = get_element_without_full_load(target_url, element_selector)
    
    if result:
        print("\n✅ 获取成功！HTML内容预览:")
        #print(result[:500] + "..." if len(result) > 500 else result)
        #print(result)
        parse_html(result)
    else:
        print("\n❌ 获取失败，请检查错误信息")