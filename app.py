import os
import json
import logging
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, jsonify, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)
CORS(app)

def fetch_doctor_page(code):
    """模拟浏览器访问同花顺诊股页面，返回HTML（使用gbk编码）"""
    url = f"https://m.10jqka.com.cn/doctor/{code}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://m.10jqka.com.cn/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        # 同花顺移动站使用gbk编码
        resp.encoding = 'gbk'
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
    """根据实际HTML结构解析关键数据"""
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # 1. 综合评分
    score_elem = soup.find('span', class_='J_compScore')
    data['score'] = score_elem.text.strip() if score_elem else 'N/A'

    # 2. 评级
    rating_elem = soup.find('div', class_='syn-advice')
    data['rating'] = rating_elem.text.strip() if rating_elem else 'N/A'

    # 3. 涨跌幅：从 hidden input stockTendency 中提取最新数据
    stock_tendency = soup.find('input', id='stockTendency')
    if stock_tendency and stock_tendency.get('value'):
        try:
            tendency_list = json.loads(stock_tendency['value'])
            if tendency_list and len(tendency_list) > 0:
                # 第一条是最近一个交易日的数据
                latest = tendency_list[0]
                data['change_percent'] = latest.get('stock', 'N/A') + '%'
            else:
                data['change_percent'] = 'N/A'
        except:
            data['change_percent'] = 'N/A'
    else:
        data['change_percent'] = 'N/A'

    # 4. 打败了xx%的股票
    beat_elem = soup.find('div', class_='syn-db')
    if beat_elem:
        beat_text = beat_elem.text
        match = re.search(r'打败了(\d+)%', beat_text)
        data['beat_percent'] = match.group(1) if match else '0'
    else:
        data['beat_percent'] = '0'

    # 5. 短期、中期、长期分析
    analysis_items = soup.find_all('li', class_='topBorder')
    # 通常前三个li分别是短期、中期、长期
    terms = ['short_term', 'mid_term', 'long_term']
    for i, term in enumerate(terms):
        if i < len(analysis_items):
            con_span = analysis_items[i].find('span', class_='J_analCon')
            data[term] = con_span.text.strip() if con_span else 'N/A'
        else:
            data[term] = 'N/A'

    # 6. 技术分析段落（在 skill 模块的第一个 p 标签）
    skill_module = soup.find('div', class_='module skill')
    if skill_module:
        tech_p = skill_module.find('div', class_='block').find('p')
        data['tech_analysis'] = tech_p.text.strip() if tech_p else 'N/A'
    else:
        data['tech_analysis'] = 'N/A'

    # 7. 压力位、支撑位、成本价
    # 在 skill 模块的下一个 block 中
    skill_blocks = skill_module.find_all('div', class_='block') if skill_module else []
    if len(skill_blocks) >= 2:
        clearfix_div = skill_blocks[1].find('div', class_='clearfix')
        if clearfix_div:
            spans = clearfix_div.find_all('span')
            # 提取数值
            for span in spans:
                text = span.text
                if '压力位' in text:
                    data['pressure'] = text.replace('压力位：', '').strip()
                elif '支撑位' in text:
                    data['support'] = text.replace('支撑位：', '').strip()
                elif '成本价' in text:
                    data['cost'] = text.replace('成本价：', '').strip()
    # 如果没有提取到，设为N/A
    data.setdefault('pressure', 'N/A')
    data.setdefault('support', 'N/A')
    data.setdefault('cost', 'N/A')

    # 8. 资金分析
    fund_module = soup.find('div', class_='module fund')
    if fund_module:
        fund_p = fund_module.find('div', class_='block').find('p')
        data['fund_analysis'] = fund_p.text.strip() if fund_p else 'N/A'
    else:
        data['fund_analysis'] = 'N/A'

    # 9. 公司分析：估值区间、盈利能力、成长能力
    company_module = soup.find('div', class_='module company')
    if company_module:
        # 估值区间：从 gzqj 中的三个 span 获取
        gzqj = company_module.find('div', class_='gzqj')
        if gzqj:
            spans = gzqj.find_all('span')
            if len(spans) >= 3:
                data['valuation_range'] = f"{spans[0].text} ~ {spans[1].text} (均价 {spans[2].text})"
            else:
                data['valuation_range'] = 'N/A'
        else:
            data['valuation_range'] = 'N/A'

        # 盈利能力和成长能力：后面的 p 标签
        p_tags = company_module.find_all('p')
        # 通常有三个 p：盈利能力、成长能力、机构预测
        for p in p_tags:
            text = p.text
            if '盈利能力' in text:
                data['profitability'] = text.strip()
            elif '成长能力' in text:
                data['growth'] = text.strip()
    # 如果没找到，设置默认值
    data.setdefault('valuation_range', 'N/A')
    data.setdefault('profitability', 'N/A')
    data.setdefault('growth', 'N/A')

    return data

@app.route('/')
def home():
    return "诊股API运行中。使用 /api/doctor?code=股票代码 获取数据，添加 &debug=1 可查看原始HTML"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/doctor', methods=['GET'])
def doctor_api():
    code = request.args.get('code', '000778')
    debug = request.args.get('debug', '0') == '1'

    logging.info(f"收到请求，股票代码: {code}, debug={debug}")

    html = fetch_doctor_page(code)
    if not html:
        logging.error(f"无法获取 {code} 的页面")
        return jsonify({'error': '无法获取页面，可能是网络问题或股票代码错误'}), 500

    if debug:
        return html

    data = parse_doctor_page(html)
    data['code'] = code
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"启动应用，监听端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
