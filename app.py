import os
import logging
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, jsonify, request
from flask_cors import CORS

# 配置日志，方便在 Railway 控制台查看错误
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
            logging.error(f"HTTP错误 {resp.status_code} for {code}")
    except requests.exceptions.Timeout:
        logging.error(f"请求超时 {url}")
    except requests.exceptions.ConnectionError:
        logging.error(f"连接错误 {url}")
    except Exception as e:
        logging.error(f"请求异常: {e}")
    return None

def parse_doctor_page(html):
    """解析HTML，提取关键数据"""
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # 综合评分
    score_elem = soup.find('div', class_='score') or soup.find('span', class_='num')
    data['score'] = score_elem.text.strip() if score_elem else 'N/A'

    # 评级
    rating_elem = soup.find('div', class_='rating') or soup.find('span', class_='tag')
    data['rating'] = rating_elem.text.strip() if rating_elem else 'N/A'

    # 涨跌幅
    change_elem = soup.find('span', class_='change') or soup.find('span', class_='price-change')
    data['change_percent'] = change_elem.text.strip() if change_elem else 'N/A'

    # 打败了xx%的股票
    beat_text = soup.find(text=re.compile(r'打败了\d+%的股票'))
    if beat_text:
        match = re.search(r'打败了(\d+)%', beat_text)
        data['beat_percent'] = match.group(1) if match else '0'
    else:
        data['beat_percent'] = '0'

    # 短中长期
    short_elem = soup.find('div', class_='short-term') or soup.find('div', class_='term-short')
    data['short_term'] = short_elem.text.strip() if short_elem else 'N/A'
    mid_elem = soup.find('div', class_='mid-term') or soup.find('div', class_='term-mid')
    data['mid_term'] = mid_elem.text.strip() if mid_elem else 'N/A'
    long_elem = soup.find('div', class_='long-term') or soup.find('div', class_='term-long')
    data['long_term'] = long_elem.text.strip() if long_elem else 'N/A'

    # 技术分析
    tech_elem = soup.find('div', class_='tech-analysis') or soup.find('div', class_='tech-desc')
    data['tech_analysis'] = tech_elem.text.strip() if tech_elem else 'N/A'

    # 压力位、支撑位、成本价
    pressure_elem = soup.find('span', class_='pressure') or soup.find('span', class_='price-pressure')
    data['pressure'] = pressure_elem.text.strip() if pressure_elem else 'N/A'
    support_elem = soup.find('span', class_='support') or soup.find('span', class_='price-support')
    data['support'] = support_elem.text.strip() if support_elem else 'N/A'
    cost_elem = soup.find('span', class_='cost') or soup.find('span', class_='price-cost')
    data['cost'] = cost_elem.text.strip() if cost_elem else 'N/A'

    # 资金分析
    fund_elem = soup.find('div', class_='fund-analysis') or soup.find('div', class_='fund-desc')
    data['fund_analysis'] = fund_elem.text.strip() if fund_elem else 'N/A'

    # 公司分析
    company_section = soup.find('div', class_='company-analysis') or soup.find('div', class_='company-info')
    if company_section:
        val_range = company_section.find('div', class_='valuation-range') or company_section.find('span', class_='range')
        data['valuation_range'] = val_range.text.strip() if val_range else 'N/A'
        profit = company_section.find('div', class_='profitability') or company_section.find('span', class_='profit')
        data['profitability'] = profit.text.strip() if profit else 'N/A'
        grow = company_section.find('div', class_='growth') or company_section.find('span', class_='grow')
        data['growth'] = grow.text.strip() if grow else 'N/A'
    else:
        data['valuation_range'] = data['profitability'] = data['growth'] = 'N/A'

    return data

@app.route('/')
def home():
    return "诊股API运行中。使用 /api/doctor?code=股票代码 获取数据"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/doctor', methods=['GET'])
def doctor_api():
    code = request.args.get('code', '000778')
    logging.info(f"收到请求，股票代码: {code}")

    html = fetch_doctor_page(code)
    if not html:
        logging.error(f"无法获取 {code} 的页面")
        return jsonify({'error': '无法获取页面，可能是网络问题或股票代码错误'}), 500

    # 调试模式：先返回HTML以查看结构（后续可注释掉）
    # return html

    data = parse_doctor_page(html)
    data['code'] = code
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"启动应用，监听端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
