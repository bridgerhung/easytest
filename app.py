import os
import time
from threading import Thread
from flask import Flask, request, send_file, render_template
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

# 創建目錄
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def delete_old_files(folder, age_in_seconds):
    """
    刪除資料夾中超過 age_in_seconds 的文件。
    """
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > age_in_seconds:
                os.remove(file_path)
                print(f"Deleted: {file_path}")

def cleanup_task():
    """
    後台清理任務，每 1 小時執行一次。
    """
    while True:
        delete_old_files(UPLOAD_FOLDER, 60)  # 刪除超過 1 小時的文件
        delete_old_files(RESULT_FOLDER, 60)
        time.sleep(60)  # 每小時執行一次

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "No file selected", 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(input_path)

    output_filename = file.filename.replace('.csv', '.xlsx')
    output_path = os.path.join(RESULT_FOLDER, output_filename)

    try:
        # 嘗試讀取 CSV 文件
        try:
            df = pd.read_csv(input_path, encoding='utf-8')  # 預設嘗試 UTF-8
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_path, encoding='big5')  # 嘗試 Big5
            except UnicodeDecodeError:
                df = pd.read_csv(input_path, encoding='ISO-8859-1')  # 最後嘗試 ISO-8859-1
        # 設置 "總時數" 為文字
        if '總時數' in df.columns:
            df['總時數'] = df['總時數'].astype(str)

        # 刪除 "登入次數"
        if '登入次數' in df.columns:
            df = df.drop(columns=['登入次數'])

        # 將結果儲存為 XLSX
        df.to_excel(output_path, index=False)

    except Exception as e:
        return f"Error processing file: {e}", 500

    return send_file(output_path, as_attachment=True)
    

if __name__ == '__main__':
    # 啟動清理任務
    cleanup_thread = Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    app.run()
