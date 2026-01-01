from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from stock_fetcher.database import get_db_storage, init_database
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中应使用更安全的密钥

@app.route('/')
def index():
    """主页，显示添加股票表单和已添加的股票列表"""
    storage = get_db_storage()
    stocks = []
    
    try:
        if storage.connect():
            stocks = storage.query_concern_stocks()
    except Exception as e:
        logger.error(f"❌ 查询股票信息失败: {e}")
        flash(f"查询股票信息失败: {e}", 'error')
    finally:
        # 注意：这里不应该关闭连接，因为storage是共享实例
        pass
    
    return render_template('index.html', stocks=stocks)

@app.route('/add_stock', methods=['POST'])
def add_stock():
    """处理添加股票请求"""
    # 获取表单数据
    stock_name = request.form.get('stock_name', '').strip()
    stock_code = request.form.get('stock_code', '').strip()
    stock_url = request.form.get('stock_url', '').strip()
    price_low = request.form.get('price_low', '').strip()
    price_high = request.form.get('price_high', '').strip()
    
    # 验证必填字段
    if not stock_name or not stock_code:
        flash('股票名称和股票代码为必填项', 'error')
        return redirect(url_for('index'))
    
    # 转换价格为数字
    try:
        price_low_val = float(price_low) if price_low else None
        price_high_val = float(price_high) if price_high else None
    except ValueError:
        flash('价格提醒值必须为数字', 'error')
        return redirect(url_for('index'))
    
    # 添加到数据库
    storage = get_db_storage()
    
    try:
        if storage.connect():
            success = storage.add_concern_stock(
                stockname=stock_name,
                stock_code=stock_code,
                stock_url=stock_url,
                price_low=price_low_val,
                price_high=price_high_val
            )
            
            if success:
                flash(f'成功添加股票: {stock_name}({stock_code})', 'success')
            else:
                flash('添加股票失败', 'error')
        else:
            flash('数据库连接失败', 'error')
    except Exception as e:
        logger.error(f"❌ 添加股票失败: {e}")
        flash(f'添加股票失败: {e}', 'error')
    finally:
        # 注意：这里不应该关闭连接，因为storage是共享实例
        pass
    
    return redirect(url_for('index'))

@app.route('/delete_stock/<int:stock_id>', methods=['POST'])
def delete_stock(stock_id):
    """删除股票"""
    storage = get_db_storage()
    
    try:
        if storage.connect():
            success = storage.delete_concern_stock(id=stock_id)
            
            if success:
                return jsonify({'success': True, 'message': '删除成功'})
            else:
                return jsonify({'success': False, 'message': '删除失败'})
        else:
            return jsonify({'success': False, 'message': '数据库连接失败'})
    except Exception as e:
        logger.error(f"❌ 删除股票失败: {e}")
        return jsonify({'success': False, 'message': f'删除失败: {e}'})
    finally:
        # 注意：这里不应该关闭连接，因为storage是共享实例
        pass

@app.route('/stocks')
def get_stocks():
    """获取股票列表API"""
    storage = get_db_storage()
    stocks = []
    
    try:
        if storage.connect():
            stocks = storage.query_concern_stocks()
    except Exception as e:
        logger.error(f"❌ 查询股票信息失败: {e}")
    finally:
        # 注意：这里不应该关闭连接，因为storage是共享实例
        pass
    
    return jsonify(stocks)

if __name__ == '__main__':
    # 初始化数据库
    if init_database():
        print("✅ 数据库已准备就绪")
    else:
        print("❌ 初始化数据库失败")
    
    app.run(debug=True, host='0.0.0.0', port=5000)