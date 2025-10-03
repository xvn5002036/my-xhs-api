from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/api/parse', methods=['GET'])
def parse_note():
    note_url = request.args.get('url')

    if not note_url:
        return jsonify({"error": "請提供 url 參數"}), 400

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        }
        response = requests.get(note_url, headers=headers)

        if response.status_code != 200:
            return jsonify({"error": f"無法訪問該網頁，狀態碼: {response.status_code}"})

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text

        return jsonify({"title": title})

    except Exception as e:
        return jsonify({"error": f"處理時發生錯誤: {e}"})

# 這個路由是為了讓 Vercel 知道服務是健康的
@app.route('/', methods=['GET'])
def index():
    return "API is running."
