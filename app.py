import os
import secrets
import string
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from github import Github
import base64

app = Flask(__name__)

# --- 設定區 ---
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = "xvn002036/my-xhs-api" # 請再次確認這是您自己的 "使用者名稱/倉庫名稱"
BINDINGS_FILE_PATH = "bindings.txt"
# --- 設定結束 ---

def get_bindings():
    """從 GitHub 獲取最新的綁定字典 {序號: 設備ID}。"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        contents = repo.get_contents(BINDINGS_FILE_PATH, ref="main")
        lines = contents.decoded_content.decode('utf-8').splitlines()
        bindings = {}
        for line in lines:
            if ',' in line:
                key, device_id = line.strip().split(',', 1)
                bindings[key] = device_id
        return bindings, contents.sha # 同時回傳 sha 以便後續更新
    except Exception:
        # 如果檔案不存在或為空，返回空字典
        return {}, None

@app.route('/api/generate_key', methods=['POST'])
def generate_key():
    if request.args.get('password') != ADMIN_PASSWORD:
        return jsonify({"status": "error", "message": "無效的管理密碼"}), 403

    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(REPO_NAME)
        
        try:
            contents = repo.get_contents(BINDINGS_FILE_PATH, ref="main")
            current_content = contents.decoded_content.decode('utf-8')
            sha = contents.sha
        except Exception: # 檔案不存在或為空
            current_content = ""
            sha = None

        letters = ''.join(secrets.choice(string.ascii_uppercase) for i in range(5))
        digits = ''.join(secrets.choice(string.digits) for i in range(12))
        new_key = f"{letters}{digits}"
        
        # 新產生的序號，設備ID設為 "UNBOUND" (未綁定)
        new_line = f"{new_key},UNBOUND"
        updated_content = current_content + "\n" + new_line if current_content else new_line
        
        if sha: # 更新檔案
            repo.update_file(BINDINGS_FILE_PATH, "Add new unbound key", updated_content, sha, "main")
        else: # 建立新檔案
            repo.create_file(BINDINGS_FILE_PATH, "Create bindings file with first key", updated_content, "main")
        
        return jsonify({"status": "success", "new_key_generated": new_key})
    except Exception as e:
        return jsonify({"status": "error", "message": f"生成序號時發生錯誤: {e}"}), 500

@app.route('/api/parse', methods=['GET'])
def parse_note():
    serial_key = request.args.get('A') # 序號
    device_id = request.args.get('B')  # 設備ID
    note_url = request.args.get('C')   # 小紅書網址

    if not all([serial_key, device_id, note_url]):
        return jsonify({"status": "error", "message": "錯誤：缺少參數 A, B, 或 C"}), 400

    bindings, sha = get_bindings()

    if sha is None:
        return jsonify({"status": "error", "message": "系統錯誤：無法讀取綁定檔案"}), 500

    if serial_key not in bindings:
        return jsonify({"status": "error", "message": "驗證失敗：無效的序號"}), 403

    stored_device_id = bindings[serial_key]

    if stored_device_id == "UNBOUND":
        # 首次使用，進行綁定
        bindings[serial_key] = device_id
        # 將更新後的綁定寫回 GitHub
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            new_content = "\n".join([f"{k},{v}" for k, v in bindings.items()])
            repo.update_file(BINDINGS_FILE_PATH, f"Bind key {serial_key} to device {device_id}", new_content, sha, "main")
        except Exception as e:
            return jsonify({"status": "error", "message": f"綁定設備時發生錯誤: {e}"}), 500
    elif stored_device_id != device_id:
        # 設備ID不符，拒絕訪問
        return jsonify({"status": "error", "message": "驗證失敗：此序號已綁定於其他設備"}), 403
    
    # 驗證通過，執行核心功能
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'}
        response = requests.get(note_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"status": "error", "message": f"無法訪問該網頁，狀態碼: {response.status_code}"})
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title').text
        
        return jsonify({"status": "success", "title": title})
    except Exception as e:
        return jsonify({"status": "error", "message": f"處理時發生錯誤: {e}"})

@app.route('/', methods=['GET'])
def index():
    return "API v6 with Device Binding is running."
