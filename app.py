# app.py
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def fetch_doctor_page(code):
    """模拟浏览器访问同花顺诊股页面"""
    url = f"https://m.10jqka.com.cn/doctor/{code}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            return resp.text
    except Exception as e:
        print(f"请求失败: {e}")
    return None

def parse_doctor_page(html):
    """解析HTML，提取关键数据"""
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # 1. 综合评分与评级
    score_elem = soup.find('div', class_='score')
    if score_elem:
        data['score'] = score_elem.text.strip()
    else:
        # 尝试其他常见类名
        score_elem = soup.find('span', class_='num')
        data['score'] = score_elem.text.strip() if score_elem else 'N/A'

    rating_elem = soup.find('div', class_='rating')
    data['rating'] = rating_elem.text.strip() if rating_elem else 'N/A'

    # 2. 涨跌幅
    change_elem = soup.find('span', class_='change')
    data['change_percent'] = change_elem.text.strip() if change_elem else 'N/A'

    # 3. 打败了xx%的股票
    beat_elem = soup.find('div', class_='beat')
    if beat_elem:
        text = beat_elem.text
        match = re.search(r'打败了(\d+)%的股票', text)
        data['beat_percent'] = match.group(1) if match else '0'
    else:
        data['beat_percent'] = '0'

    # 4. 短期、中期、长期分析
    short_term = soup.find('div', class_='term-item short')
    data['short_term'] = short_term.text.strip() if short_term else 'N/A'

    mid_term = soup.find('div', class_='term-item mid')
    data['mid_term'] = mid_term.text.strip() if mid_term else 'N/A'

    long_term = soup.find('div', class_='term-item long')
    data['long_term'] = long_term.text.strip() if long_term else 'N/A'

    # 5. 技术分析段落
    tech_section = soup.find('div', class_='tech-analysis')
    data['tech_analysis'] = tech_section.text.strip() if tech_section else 'N/A'

    # 6. 压力位、支撑位、成本价
    pressure = soup.find('span', class_='pressure')
    data['pressure'] = pressure.text.strip() if pressure else 'N/A'
    support = soup.find('span', class_='support')
    data['support'] = support.text.strip() if support else 'N/A'
    cost = soup.find('span', class_='cost')
    data['cost'] = cost.text.strip() if cost else 'N/A'

    # 7. 资金分析
    fund_section = soup.find('div', class_='fund-analysis')
    data['fund_analysis'] = fund_section.text.strip() if fund_section else 'N/A'

    # 8. 公司分析：估值区间、盈利能力、成长能力
    company_section = soup.find('div', class_='company-analysis')
    if company_section:
        data['valuation_range'] = company_section.find('div', class_='range').text.strip() if company_section.find('div', class_='range') else 'N/A'
        data['profitability'] = company_section.find('div', class_='profitability').text.strip() if company_section.find('div', class_='profitability') else 'N/A'
        data['growth'] = company_section.find('div', class_='growth').text.strip() if company_section.find('div', class_='growth') else 'N/A'
    else:
        data['valuation_range'] = 'N/A'
        data['profitability'] = 'N/A'
        data['growth'] = 'N/A'

    return data

@app.route('/api/doctor', methods=['GET'])
def doctor_api():
    code = request.args.get('code', '000778')
    html = fetch_doctor_page(code)
    if not html:
        return jsonify({'error': '无法获取页面'}), 500

    data = parse_doctor_page(html)
    data['code'] = code
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)