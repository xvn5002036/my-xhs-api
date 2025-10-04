import os
import secrets
import string
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from github import Github
import json
import traceback

app = Flask(__name__)

# --- 設定區 (請再次確認 REPO_NAME 是否正確) ---
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = "xvn5002036/my-xhs-api" # 請務必使用您自己的 "使用者名稱/倉庫名稱"
BINDINGS_FILE_PATH = "bindings.txt"
# --- 設定結束 ---

# ... (get_bindings 函數維持不變) ...
def get_bindings():
    # ... (此處程式碼省略，與之前版本相同) ...
    pass

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
        except Exception: 
            current_content = ""
            sha = None

        letters = ''.join(secrets.choice(string.ascii_uppercase) for i in range(5))
        digits = ''.join(secrets.choice(string.digits) for i in range(12))
        new_key = f"{letters}{digits}"
        
        new_line = f"{new_key},UNBOUND"
        
        # --- 這是我們修正的核心邏輯 ---
        # 移除現有內容前後多餘的空白行
        current_content_stripped = current_content.strip()
        
        if current_content_stripped:
            # 如果檔案已有內容，則換行後再加入新序號
            updated_content = current_content_stripped + "\n" + new_line
        else:
            # 如果檔案是空的，則直接寫入新序號，不加換行
            updated_content = new_line
        # --- 修正結束 ---
        
        if sha:
            repo.update_file(BINDINGS_FILE_PATH, "Add new unbound key", updated_content, sha, "main")
        else:
            repo.create_file(BINDINGS_FILE_PATH, "Create bindings file with first key", updated_content, "main")
        
        return jsonify({"status": "success", "new_key_generated": new_key})

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"生成序號時發生錯誤: {e}"}), 500

# ... (parse_note 和 index 函數維持不變) ...
@app.route('/api/parse', methods=['GET'])
def parse_note():
    # ... (此處程式碼省略，與之前版本相同) ...
    pass

@app.route('/', methods=['GET'])
def index():
    return "API v8 with Blank Line Fix is running."

# 以下為完整的程式碼，請直接複製使用
import os
import secrets
import string
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from github import Github
import json
import traceback

app = Flask(__name__)

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = "xvn5002036/my-xhs-api"
BINDINGS_FILE_PATH = "bindings.txt"

def get_bindings():
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
        return bindings, contents.sha
    except Exception:
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
        except Exception:
            current_content = ""
            sha = None

        letters = ''.join(secrets.choice(string.ascii_uppercase) for i in range(5))
        digits = ''.join(secrets.choice(string.digits) for i in range(12))
        new_key = f"{letters}{digits}"
        
        new_line = f"{new_key},UNBOUND"
        
        current_content_stripped = current_content.strip()
        
        if current_content_stripped:
            updated_content = current_content_stripped + "\n" + new_line
        else:
            updated_content = new_line
        
        if sha:
            repo.update_file(BINDINGS_FILE_PATH, "Add new unbound key", updated_content, sha, "main")
        else:
            repo.create_file(BINDINGS_FILE_PATH, "Create bindings file with first key", updated_content, "main")
        
        return jsonify({"status": "success", "new_key_generated": new_key})
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"生成序號時發生錯誤: {e}"}), 500

@app.route('/api/parse', methods=['GET'])
def parse_note():
    serial_key = request.args.get('A')
    device_id = request.args.get('B')
    note_url = request.args.get('C')

    if not all([serial_key, device_id, note_url]):
        return jsonify({"status": "error", "message": "錯誤：缺少參數 A, B, 或 C"}), 400

    bindings, sha = get_bindings()

    if sha is None:
        return jsonify({"status": "error", "message": "系統錯誤：無法讀取綁定檔案"}), 500

    if serial_key not in bindings:
        return jsonify({"status": "error", "message": "驗證失敗：無效的序號"}), 403

    stored_device_id = bindings[serial_key]

    if stored_device_id == "UNBOUND":
        bindings[serial_key] = device_id
        try:
            g = Github(GITHUB_TOKEN)
            repo = g.get_repo(REPO_NAME)
            new_content = "\n".join([f"{k},{v}" for k, v in bindings.items()])
            repo.update_file(BINDINGS_FILE_PATH, f"Bind key {serial_key} to device {device_id}", new_content, sha, "main")
        except Exception as e:
            print(traceback.format_exc())
            return jsonify({"status": "error", "message": f"綁定設備時發生錯誤: {e}"}), 500
    elif stored_device_id != device_id:
        return jsonify({"status": "error", "message": "驗證失敗：此序號已綁定於其他設備"}), 403
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'}
        response = requests.get(note_url, headers=headers)
        if response.status_code != 200:
            return jsonify({"status": "error", "message": f"無法訪問該網頁，狀態碼: {response.status_code}"})
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        script_tag = soup.find('script', string=lambda t: t and 'window.__INITIAL_STATE__' in t)
        if not script_tag:
            return jsonify({"status": "error", "message": "解析失敗：找不到筆記資料"})
            
        json_data_str = script_tag.string.split('=', 1)[1].strip()
        if json_data_str.endswith('</script>'):
            json_data_str = json_data_str[:-9]

        json_data = json.loads(json_data_str)
        
        note_data = list(json_data['note']['noteDetailMap'].values())[0]['note']
        
        note_type = note_data.get('type')
        title = note_data.get('title')
        media_urls = []

        if note_type == 'video':
            notetype_for_shortcut = "video"
            video_info = note_data['video']['stream']['h264'][0]
            media_urls.append(video_info['url'])
        else:
            notetype_for_shortcut = "image"
            for image_info in note_data.get('imageList', []):
                highest_quality_url = image_info['urlDefault']
                for res in image_info['infoList']:
                    if res['imageScene'] == 'CRD_WM_WEBP':
                        highest_quality_url = res['url']
                        break
                media_urls.append(highest_quality_url)
        
        return jsonify({
            "status": "success",
            "title": title,
            "notetype": notetype_for_shortcut,
            "media_urls": media_urls
        })

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"status": "error", "message": f"處理時發生錯誤: {e}"}), 500

@app.route('/', methods=['GET'])
def index():
    return "API v8 with Blank Line Fix is running."
