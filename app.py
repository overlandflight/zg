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
CORS(app, origins="*")  # 允许所有来源跨域

def fetch_doctor_page(code):
    url = f"https://m.10jqka.com.cn/doctor/{code}/"
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://m.10jqka.com.cn/",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        resp.encoding = 'gbk'
        if resp.status_code == 200:
            logging.info(f"成功获取 {code} 页面，长度 {len(resp.text)}")
            return resp.text
        else:
            logging.error(f"HTTP错误 {resp.status_code} for {code}")
    except Exception as e:
        logging.error(f"请求异常: {e}")
    return None

def parse_doctor_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # ----- 股票名称 -----
    stock_name_elem = soup.find('div', class_='stockName')
    if stock_name_elem:
        full_text = stock_name_elem.text.strip()
        # 格式如 "新兴铸管(000778)"，提取括号前的内容
        name_part = full_text.split('(')[0].strip()
        data['stock_name'] = name_part if name_part else full_text
    else:
        data['stock_name'] = 'N/A'

    # ----- 文本数据 -----
    score_elem = soup.find('span', class_='J_compScore')
    data['score'] = score_elem.text.strip() if score_elem else 'N/A'
    rating_elem = soup.find('div', class_='syn-advice')
    data['rating'] = rating_elem.text.strip() if rating_elem else 'N/A'
    stock_tendency = soup.find('input', id='stockTendency')
    if stock_tendency and stock_tendency.get('value'):
        try:
            tendency_list = json.loads(stock_tendency['value'])
            if tendency_list:
                latest = tendency_list[0]
                data['change_percent'] = latest.get('stock', 'N/A') + '%'
            else:
                data['change_percent'] = 'N/A'
        except:
            data['change_percent'] = 'N/A'
    else:
        data['change_percent'] = 'N/A'
    beat_elem = soup.find('div', class_='syn-db')
    if beat_elem:
        beat_text = beat_elem.text
        match = re.search(r'打败了(\d+)%', beat_text)
        data['beat_percent'] = match.group(1) if match else '0'
    else:
        data['beat_percent'] = '0'
    analysis_items = soup.find_all('li', class_='topBorder')
    terms = ['short_term', 'mid_term', 'long_term']
    for i, term in enumerate(terms):
        if i < len(analysis_items):
            con_span = analysis_items[i].find('span', class_='J_analCon')
            data[term] = con_span.text.strip() if con_span else 'N/A'
        else:
            data[term] = 'N/A'
    skill_module = soup.find('div', class_='module skill')
    if skill_module:
        tech_p = skill_module.find('div', class_='block').find('p')
        data['tech_analysis'] = tech_p.text.strip() if tech_p else 'N/A'
    else:
        data['tech_analysis'] = 'N/A'
    skill_blocks = skill_module.find_all('div', class_='block') if skill_module else []
    if len(skill_blocks) >= 2:
        clearfix_div = skill_blocks[1].find('div', class_='clearfix')
        if clearfix_div:
            spans = clearfix_div.find_all('span')
            for span in spans:
                text = span.text
                if '压力位' in text:
                    data['pressure'] = text.replace('压力位：', '').strip()
                elif '支撑位' in text:
                    data['support'] = text.replace('支撑位：', '').strip()
                elif '成本价' in text:
                    data['cost'] = text.replace('成本价：', '').strip()
    data.setdefault('pressure', 'N/A')
    data.setdefault('support', 'N/A')
    data.setdefault('cost', 'N/A')
    fund_module = soup.find('div', class_='module fund')
    if fund_module:
        fund_p = fund_module.find('div', class_='block').find('p')
        data['fund_analysis'] = fund_p.text.strip() if fund_p else 'N/A'
    else:
        data['fund_analysis'] = 'N/A'
    company_module = soup.find('div', class_='module company')
    if company_module:
        gzqj = company_module.find('div', class_='gzqj')
        if gzqj:
            spans = gzqj.find_all('span')
            if len(spans) >= 3:
                data['valuation_range'] = f"{spans[0].text} ~ {spans[1].text} (均价 {spans[2].text})"
            else:
                data['valuation_range'] = 'N/A'
        else:
            data['valuation_range'] = 'N/A'
        p_tags = company_module.find_all('p')
        for p in p_tags:
            text = p.text
            if '盈利能力' in text:
                data['profitability'] = text.strip()
            elif '成长能力' in text:
                data['growth'] = text.strip()
    data.setdefault('valuation_range', 'N/A')
    data.setdefault('profitability', 'N/A')
    data.setdefault('growth', 'N/A')

    # ----- 图表数据 -----
    allcatescore_input = soup.find('input', id='allcatescore')
    if allcatescore_input and allcatescore_input.get('value'):
        try:
            radar_data = json.loads(allcatescore_input['value'])
            for k in radar_data:
                radar_data[k] = float(radar_data[k])
            data['radar_data'] = radar_data
        except:
            data['radar_data'] = {}
    else:
        data['radar_data'] = {}
    if stock_tendency and stock_tendency.get('value'):
        try:
            tech_history = json.loads(stock_tendency['value'])
            data['tech_history'] = tech_history
        except:
            data['tech_history'] = []
    else:
        data['tech_history'] = []
    chart_data_div = soup.find('div', id='chartData')
    if chart_data_div and chart_data_div.text:
        try:
            fund_history = json.loads(chart_data_div.text)
            data['fund_history'] = fund_history
        except:
            data['fund_history'] = []
    else:
        data['fund_history'] = []

    # ----- 机构分析 -----
    institution_module = soup.find('div', class_='module institution')
    if institution_module:
        attention_p = institution_module.find('div', class_='block').find('p')
        data['institution_attention'] = attention_p.text.strip() if attention_p else 'N/A'
        blocks = institution_module.find_all('div', class_='block')
        if len(blocks) >= 2:
            position_p = blocks[1].find('p')
            data['institution_position'] = position_p.text.strip() if position_p else 'N/A'
        else:
            data['institution_position'] = 'N/A'
        table = institution_module.find('table', class_='jigou-table')
        if table and table.find('tbody').find_all('tr'):
            rows = []
            for tr in table.find('tbody').find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) >= 4:
                    rows.append({
                        'org': tds[0].text.strip(),
                        'rating': tds[1].text.strip(),
                        'direction': tds[2].text.strip(),
                        'prev_rating': tds[3].text.strip()
                    })
            data['institution_table'] = rows
        else:
            data['institution_table'] = []
    else:
        data['institution_attention'] = 'N/A'
        data['institution_position'] = 'N/A'
        data['institution_table'] = []

    return data

@app.route('/')
def home():
    return "诊股API运行中。使用 /api/doctor?code=股票代码 获取数据（含图表数据），添加 &debug=1 可查看原始HTML"

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
        return jsonify({'error': '无法获取页面'}), 500

    if debug:
        return html

    data = parse_doctor_page(html)
    data['code'] = code
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"启动应用，监听端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
