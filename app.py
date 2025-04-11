from flask import Flask, request, send_file, session, render_template, after_this_request, jsonify
import os
import time
import pandas as pd
import requests
from threading import Thread
from werkzeug.utils import secure_filename

from config import UPLOAD_FOLDER, RESULT_FOLDER, SECRET_KEY, SESSION_LIFETIME, TURNSTILE_SECRET_KEY
from utils.file_ops import delete_old_files
from services.processor import process_online_info, process_score_report, process_easytest
from utils.time_parser import parse_time_to_seconds, parse_myet_time_to_seconds, seconds_to_hour_minute 

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_LIFETIME


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def cleanup_task():
    while True:
        delete_old_files(UPLOAD_FOLDER, 60)
        delete_old_files(RESULT_FOLDER, 60)
        time.sleep(60)

@app.route('/')
def home():
    return render_template("home.html")

@app.route('/new')
def new():
    show_captcha = 'captcha_verified' not in session or not session['captcha_verified']
    return render_template('new.html', show_captcha=show_captcha)

@app.route('/legacy')
def legacy():
    show_captcha = 'captcha_verified' not in session or not session['captcha_verified']
    return render_template('legacy.html', show_captcha=show_captcha)

@app.route('/new/upload', methods=['POST'])
def upload_file():
    
    if 'captcha_verified' in session and session['captcha_verified']:
        pass  # 跳過 CAPTCHA 驗證
    else:
        captcha_token = request.form.get('cf-turnstile-response')
        if not captcha_token:
            return {"error": "CAPTCHA token is missing"}, 400

        verification_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": TURNSTILE_SECRET_KEY,
            "response": captcha_token,
            "remoteip": request.remote_addr
        }
        response = requests.post(verification_url, data=payload)
        result = response.json()

        if not result.get("success"):
            return {"error": "CAPTCHA validation failed"}, 403

        session['captcha_verified'] = True
        session.permanent = True
    
    if 'history_file' not in request.files or 'online_info_file' not in request.files:
        return "請上傳 history*.csv 和 OnlineInfo_*.xlsx 檔案", 400

    history_file = request.files['history_file']
    online_info_file = request.files['online_info_file']

    if history_file.filename == '' or online_info_file.filename == '':
        return "沒有檔案被選取", 400

    if not history_file.filename.lower().endswith('.csv'):
        return "History 檔案必須是 .csv 格式", 400

    if not online_info_file.filename.lower().endswith('.xlsx'):
        return "OnlineInfo 檔案必須是 .xlsx 格式", 400

    try:
        history_path = os.path.join(UPLOAD_FOLDER, secure_filename(history_file.filename))
        online_info_path = os.path.join(UPLOAD_FOLDER, secure_filename(online_info_file.filename))
        history_file.save(history_path)
        online_info_file.save(online_info_path)

        # 讀取 history.csv
        try:
            history_df = pd.read_csv(history_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                history_df = pd.read_csv(history_path, encoding='big5')
            except UnicodeDecodeError:
                history_df = pd.read_csv(history_path, encoding='ISO-8859-1')

        history_df = history_df.astype(str)

        # 處理不同的上傳類型
        filename = online_info_file.filename

        if filename.endswith("Stud_List.xlsx"):
            stud_df = pd.read_excel(
                online_info_path,
                sheet_name=0,
                skiprows=4,
                usecols=[0, 1, 2, 3],
                names=["班級", "學號", "姓名", "修別"]
            )
            result_df = process_easytest(stud_df, history_df)
            result_filename = "result_stud_list.xlsx"

        elif filename.startswith("ScoreReport"):
            score_df = pd.read_excel(
                online_info_path,
                sheet_name=0,
                skiprows=1,
                usecols=["帳號", "名字", "上線時間", "平均分數", "次"]
            )
            result_df = process_score_report(score_df, history_df)
            result_filename = "result_score_report.xlsx"

        elif filename.startswith("OnlineInfo"):
            online_df = pd.read_excel(
                online_info_path,
                sheet_name=0,
                skiprows=1,
                usecols=["帳號", "姓名", "總上線時間", "登入學習次數"]
            )
            result_df = process_online_info(online_df, history_df)
            result_df.rename(columns={"總時數": "EasyTest總時數"}, inplace=True)
            result_filename = "result_online_info.xlsx"
    
        else:
            return "不支援的檔案格式", 400

        result_path = os.path.join(RESULT_FOLDER, result_filename)
        result_df.to_excel(result_path, index=False)

        @after_this_request
        def cleanup(response):
            try:
                os.remove(history_path)
                os.remove(online_info_path)
                os.remove(result_path)
            except Exception as e:
                print(f"清理時發生錯誤: {e}")
            return response

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        return f"處理檔案時發生錯誤: {str(e)}", 500


@app.route('/legacy/upload', methods=['POST'])
def legacy_upload():
    if 'captcha_verified' in session and session['captcha_verified']:
        pass  # 跳過 CAPTCHA 驗證
    else:
        captcha_token = request.form.get('cf-turnstile-response')
        if not captcha_token:
            return {"error": "CAPTCHA token is missing"}, 400

        verification_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": TURNSTILE_SECRET_KEY,
            "response": captcha_token,
            "remoteip": request.remote_addr
        }
        response = requests.post(verification_url, data=payload)
        result = response.json()

        if not result.get("success"):
            return {"error": "CAPTCHA validation failed"}, 403

        session['captcha_verified'] = True
        session.permanent = True

    if 'file' not in request.files:
        return {"error": "請上傳檔案"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "未選擇檔案"}, 400

    filename = secure_filename(file.filename)

    if not (filename.lower().endswith('.xlsx') or filename.lower().endswith('.csv')):
        return {"error": "檔案格式不支援，請上傳 .xlsx 或 .csv 檔案"}, 400

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    name, ext = os.path.splitext(filename)
    output_filename = f"{name}-count.xlsx"
    output_path = os.path.join(RESULT_FOLDER, output_filename)

    try:
        if filename.startswith('OnlineInfo') and ext == '.xlsx':
            df = pd.read_excel(input_path, skiprows=1, usecols=["帳號", "姓名", "總上線時間", "登入學習次數"])
            df["MyET秒數"] = df["總上線時間"].apply(parse_myet_time_to_seconds)
            df["MyET時分"] = df["MyET秒數"].apply(seconds_to_hour_minute)
            df.to_excel(output_path, index=False)

        elif filename.startswith('ScoreReport') and ext == '.xlsx':
            df = pd.read_excel(input_path, skiprows=1, usecols=["帳號", "名字", "上線時間"])
            df["MyET秒數"] = df["上線時間"].apply(parse_myet_time_to_seconds)
            df.to_excel(output_path, index=False)

        else:
            try:
                df = pd.read_csv(input_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_path, encoding='big5')
                except UnicodeDecodeError:
                    df = pd.read_csv(input_path, encoding='ISO-8859-1')

            df["總時數"] = df["總時數"].astype(str)
            df["秒數"] = df["總時數"].apply(parse_time_to_seconds)
            df.to_excel(output_path, index=False)

        @after_this_request
        def remove_files(response):
            try:
                os.remove(input_path)
                os.remove(output_path)
            except Exception as e:
                print(f"Error deleting files: {e}")
            return response

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        if os.path.exists(input_path):
            os.remove(input_path)
        return {"error": str(e)}, 500

if __name__ == '__main__':
    cleanup_thread = Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)