import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS

# 配置日志，方便在Railway控制台查看错误
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

def fetch_doctor_page(code):
    """模拟浏览器访问同花顺诊股页面，返回HTML"""
    url = f"https://m.10jqka.com.cn/doctor/{code}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://m.10jqka.com.cn/",
    }
    try:
        # 设置超时，避免长时间阻塞
        resp = requests.get(url, headers=headers, timeout=8)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            logging.info(f"成功获取 {code} 页面，长度 {len(resp.text)}")
            return resp.text
        else:
            logging.error(f"HTTP错误 {resp.status_code}  for {code}")
    except requests.exceptions.Timeout:
        logging.error(f"请求超时 {url}")
    except requests.exceptions.ConnectionError:
        logging.error(f"连接错误 {url}")
    except Exception as e:
        logging.error(f"请求异常: {e}")
    return None

@app.route('/')
def home():
    return "诊股API运行中。使用 /api/doctor?code=000778 获取数据（当前为调试模式，返回HTML）"

@app.route('/health')
def health():
    """健康检查，确认服务是否存活"""
    return "OK", 200

@app.route('/api/doctor', methods=['GET'])
def doctor_api():
    code = request.args.get('code', '000778')
    logging.info(f"收到请求，股票代码: {code}")

    html = fetch_doctor_page(code)
    if not html:
        logging.error(f"无法获取 {code} 的页面")
        return jsonify({'error': '无法获取页面，可能是网络问题或股票代码错误'}), 500

    # ========== 调试模式：直接返回原始 HTML ==========
    # 此时返回的是 text/html 内容，方便查看页面结构
    logging.info(f"返回 {code} 的原始HTML，长度 {len(html)}")
    return html
    # ===============================================

    # 正常模式下，取消下面注释，并注释掉上面的 return html
    # data = parse_doctor_page(html)
    # data['code'] = code
    # return jsonify(data)

def parse_doctor_page(html):
    """解析HTML，提取关键数据（暂未使用，保留供后续）"""
    soup = BeautifulSoup(html, 'html.parser')
    data = {}
    # ... 解析逻辑（可以从之前的代码复制）...
    return data

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"启动应用，监听端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)  # 生产环境关闭debug
