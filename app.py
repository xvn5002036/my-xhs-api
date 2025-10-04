from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- 設定區 ---
# 請將這裡的連結換成您自己 GitHub 倉庫中 keys.txt 的 "Raw" 連結
# 如何取得 Raw 連結: 點開 keys.txt 檔案 -> 點擊 "Raw" 按鈕 -> 複製瀏覽器網址列的連結
KEYS_URL = "https://raw.githubusercontent.com/xvn5002036/my-xhs-api/refs/heads/main/app.py"
# --- 設定結束 ---

def get_valid_keys():
    """從 GitHub 獲取最新的有效序號列表。"""
    try:
        response = requests.get(KEYS_URL)
        if response.status_code == 200:
            # 將文字內容按行分割，並去除每行可能存在的空白
            keys = [key.strip() for key in response.text.splitlines() if key.strip()]
            return keys
        return None
    except Exception:
        return None

@app.route('/api/parse', methods=['GET'])
def parse_note():
    # --- 1. 接收與驗證參數 ---
    
    # C: 取得小紅書網址 (必要)
    note_url = request.args.get('C')
    if not note_url:
        return jsonify({"status": "error", "message": "錯誤：未提供參數 C (小紅書網址)"}), 400

    # A: 取得序號 (必要)
    serial_key = request.args.get('A')
    if not serial_key:
        return jsonify({"status": "error", "message": "錯誤：未提供參數 A (序號)"}), 400

    # B: 取得主機詳細訊息 (選用)
    host_info = request.args.get('B', '未提供') # 如果沒提供，預設為'未提供'

    # --- 2. 序號驗證 ---
    
    valid_keys = get_valid_keys()
    
    if valid_keys is None:
        return jsonify({"status": "error", "message": "系統錯誤：無法從 GitHub 獲取序號列表"}), 500

    if serial_key not in valid_keys:
        return jsonify({"status": "error", "message": "驗證失敗：無效的序號"}), 403 # 403 代表禁止訪問

    # --- 3. 執行核心功能 (序號驗證通過後) ---
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
        }
        response = requests.get(note_url, headers=headers)
        
        if response.status_code != 200:
            return jsonify({"status": "error", "message": f"無法訪問該網頁，狀態碼: {response.status_code}"})

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text
        
        # --- 4. 回傳成功結果 ---
        
        return jsonify({
            "status": "success",
            "title": title,
            "host_info_received": host_info # 將收到的 B 參數回傳，以確認
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"處理時發生錯誤: {e}"})

@app.route('/', methods=['GET'])
def index():
    return "API v3 with Authentication is running."
