def parse_doctor_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    data = {}

    # ----- 原有文本数据（保持不变）-----
    # 综合评分
    score_elem = soup.find('span', class_='J_compScore')
    data['score'] = score_elem.text.strip() if score_elem else 'N/A'
    # 评级
    rating_elem = soup.find('div', class_='syn-advice')
    data['rating'] = rating_elem.text.strip() if rating_elem else 'N/A'
    # 涨跌幅
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
    # 打败比例
    beat_elem = soup.find('div', class_='syn-db')
    if beat_elem:
        beat_text = beat_elem.text
        match = re.search(r'打败了(\d+)%', beat_text)
        data['beat_percent'] = match.group(1) if match else '0'
    else:
        data['beat_percent'] = '0'
    # 短中长期
    analysis_items = soup.find_all('li', class_='topBorder')
    terms = ['short_term', 'mid_term', 'long_term']
    for i, term in enumerate(terms):
        if i < len(analysis_items):
            con_span = analysis_items[i].find('span', class_='J_analCon')
            data[term] = con_span.text.strip() if con_span else 'N/A'
        else:
            data[term] = 'N/A'
    # 技术分析
    skill_module = soup.find('div', class_='module skill')
    if skill_module:
        tech_p = skill_module.find('div', class_='block').find('p')
        data['tech_analysis'] = tech_p.text.strip() if tech_p else 'N/A'
    else:
        data['tech_analysis'] = 'N/A'
    # 压力位、支撑位、成本价
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
    # 资金分析
    fund_module = soup.find('div', class_='module fund')
    if fund_module:
        fund_p = fund_module.find('div', class_='block').find('p')
        data['fund_analysis'] = fund_p.text.strip() if fund_p else 'N/A'
    else:
        data['fund_analysis'] = 'N/A'
    # 公司分析
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

    # ----- 图表数据（保持不变）-----
    # 1. 综合评分细分（用于雷达图）
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

    # 2. 技术走势历史数据（用于折线图）
    if stock_tendency and stock_tendency.get('value'):
        try:
            tech_history = json.loads(stock_tendency['value'])
            data['tech_history'] = tech_history
        except:
            data['tech_history'] = []
    else:
        data['tech_history'] = []

    # 3. 资金流向历史数据（用于柱状图）
    chart_data_div = soup.find('div', id='chartData')
    if chart_data_div and chart_data_div.text:
        try:
            fund_history = json.loads(chart_data_div.text)
            data['fund_history'] = fund_history
        except:
            data['fund_history'] = []
    else:
        data['fund_history'] = []

    # ----- 新增：机构分析 -----
    institution_module = soup.find('div', class_='module institution')
    if institution_module:
        # 机构关注度描述（第一个 p 标签）
        attention_p = institution_module.find('div', class_='block').find('p')
        data['institution_attention'] = attention_p.text.strip() if attention_p else 'N/A'

        # 机构持仓变化描述（第二个 block 中的 p 标签）
        blocks = institution_module.find_all('div', class_='block')
        if len(blocks) >= 2:
            position_p = blocks[1].find('p')
            data['institution_position'] = position_p.text.strip() if position_p else 'N/A'
        else:
            data['institution_position'] = 'N/A'

        # 可选：提取机构评级表格（如果有数据）
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
