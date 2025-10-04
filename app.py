import os
import secrets  # 使用更安全的隨機數生成器
import string   # 引入字元集，方便選取英文和數字
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from github import Github

app = Flask(__name__)

# --- 設定區 ---
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = "xvn5002036/my-xhs-api" # 請確認這是您自己的 "使用者名稱/倉庫名稱"
KEYS_FILE_PATH = "keys.txt"
KEYS_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{KEYS_FILE_PATH}"
# --- 設定結束 ---

def get_valid_keys():
    """從 GitHub 獲取最新的有效序號列表。"""
    try:
        response = requests.get(KEYS_URL)
        if response.status_code == 200:
            keys = [key.strip() for key in response.text.splitlines() if key.strip()]
            return keys
        return None
    except Exception:
        return None

@app.route('/api/generate_key', methods=['POST'])
def generate_key():
    provided_password = request.args.get('password')
    if provided_password != ADMIN_PASSWORD:
        return jsonify({"status": "error", "message": "無效的管理密碼"}), 403

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(KEYS_FILE_PATH, ref="main")
        current_keys = contents.decoded_content.decode('utf-8')
        
        # --- 這裡是我們修改的核心 ---
        # 1. 從 A-Z 中隨機選擇 5 個大寫英文字母
        letters = ''.join(secrets.choice(string.ascii_uppercase) for i in range(5))
        # 2. 從 0-9 中隨機選擇 12 個數字
        digits = ''.join(secrets.choice(string.digits) for i in range(12))
        # 3. 將它們組合成新的序號格式
        new_key = f"{letters}{digits}"
        # --- 修改結束 ---
        
        updated_content = current_keys + "\n" + new_key
        
        repo.update_file(
            path=KEYS_FILE_PATH,
            message="Automatically add new key in custom format",
            content=updated_content,
            sha=contents.sha,
            branch="main"
        )
        
        return jsonify({"status": "success", "new_key_generated": new_key})

    except Exception as e:
        return jsonify({"status": "error", "message": f"生成序號時發生錯誤: {e}"}), 500

@app.route('/api/parse', methods=['GET'])
def parse_note():
    serial_key = request.args.get('A')
    note_url = request.args.get('C')
    host_info = request.args.get('B', '未提供')

    if not note_url or not serial_key:
        return jsonify({"status": "error", "message": "錯誤：缺少參數 A 或 C"}), 400

    valid_keys = get_valid_keys()
    if valid_keys is None or serial_key not in valid_keys:
        return jsonify({"status": "error", "message": "驗證失敗：無效的序號"}), 403

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'}
        response = requests.get(note_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"status": "error", "message": f"無法訪問該網頁，狀態碼: {response.status_code}"})
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text
        
        return jsonify({"status": "success", "title": title, "host_info_received": host_info})
    except Exception as e:
        return jsonify({"status": "error", "message": f"處理時發生錯誤: {e}"})

@app.route('/', methods=['GET'])
def index():
    return "API v5 with Custom Key Format is running."
