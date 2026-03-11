import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "诊股API测试版"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/doctor', methods=['GET'])
def doctor_api():
    # 直接返回静态 HTML，不请求外部网站
    code = request.args.get('code', '000778')
    logging.info(f"收到请求，股票代码: {code}")
    return """
    <html>
        <body>
            <h1>测试页面</h1>
            <p>这是静态返回的内容，证明服务正常。</p>
            <p>请求的代码是：""" + code + """</p>
        </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logging.info(f"启动应用，监听端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
