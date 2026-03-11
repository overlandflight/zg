import os
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

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
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"HTTP错误: {resp.status_code}")
    except Exception as e:
        print(f"请求异常: {e}")
    return None

def parse_doctor_page(html):
    """解析HTML，提取关键数据（当前调试阶段暂未使用）"""
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
    return "股吧弹幕后端服务运行中，请访问 /api/doctor?code=股票代码 获取诊股数据（调试模式返回HTML）"

@app.route('/api/doctor', methods=['GET'])
def doctor_api():
    code = request.args.get('code', '000778')
    html = fetch_doctor_page(code)
    if not html:
        return jsonify({'error': '无法获取页面'}), 500

    # ========== 调试模式：直接返回原始 HTML ==========
    # 此时返回的是 text/html 内容，方便查看页面结构
    return html
    # ===============================================

    # 正常模式下，取消下面注释，并注释掉上面的 return html
    # data = parse_doctor_page(html)
    # data['code'] = code
    # return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
