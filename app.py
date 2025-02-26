from flask import Flask, render_template, request, send_file, after_this_request, redirect, url_for, session
import os
import time
import pandas as pd
from datetime import datetime, timedelta
from threading import Thread
from openpyxl import load_workbook
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")
app.secret_key = '@Your_secret_Key'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def delete_old_files(folder, age_in_seconds):
    """Delete files older than age_in_seconds in the specified folder."""
    now = time.time()
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            file_age = now - os.path.getmtime(file_path)
            if file_age > age_in_seconds:
                os.remove(file_path)
                print(f"Deleted: {file_path}")

def cleanup_task():
    """Background cleanup task, runs every hour."""
    while True:
        delete_old_files(UPLOAD_FOLDER, 60)
        delete_old_files(RESULT_FOLDER, 60)
        time.sleep(60)

@app.route('/')
def homepage():
    return render_template('home.html')

@app.route('/legacy')
def legacy():
    show_captcha = 'captcha_verified' not in session or not session['captcha_verified']
    return render_template('legacy.html', show_captcha=show_captcha)

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

    # 原有檔案處理邏輯...

    if 'file' not in request.files:
        return {"error": "請上傳檔案"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "未選擇檔案"}, 400

    filename = secure_filename(file.filename)
    
    if not (filename.lower().endswith('.xlsx') or filename.lower().endswith('.csv')):
        return {"error": "檔案格式不支援，請上傳 .xlsx 或 .csv 檔案"}, 400

    try:
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}-count.xlsx"
        output_path = os.path.join(RESULT_FOLDER, output_filename)

        if filename.startswith('OnlineInfo') and filename.lower().endswith('.xlsx'):
            # MyET xlsx 處理邏輯
            wb = load_workbook(input_path)
            ws = wb.active

            # 秒數欄位 E
            ws["E2"] = "秒數"
            max_row = ws.max_row
            for i in range(3, max_row + 1):
                c_cell = f"C{i}"
                e_cell = f"E{i}"
                formula_e = '=IFERROR(LEFT({},FIND("天",{})-1)*86400,0) + IFERROR(MID({},FIND("天",{})+2,FIND("小時",{})-FIND("天",{})-2)*3600,0) + IFERROR(MID({},FIND("小時",{})+2,FIND("分",{})-FIND("小時",{})-2)*60,0) + IFERROR(MID({},FIND("分",{})+2,FIND("秒",{})-FIND("分",{})-2),0)'.format(
                    c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell,c_cell
                )
                ws[e_cell] = formula_e



            # 時分欄位 G
            ws["G2"] = "時分"
            for i in range(3, max_row + 1):
                e_cell = f"E{i}"
                g_cell = f"G{i}"
                formula_g = '=TEXT(INT({}/3600),"00")&"時"&TEXT(INT(MOD({},3600)/60),"00")&"分"'.format(e_cell, e_cell)
                ws[g_cell] = formula_g

            wb.save(output_path)
        elif filename.startswith('ScoreReport') and filename.lower().endswith('.xlsx'):
            # Add formulas
            wb = load_workbook(input_path)
            ws = wb.active
            # 將上線時間(第三欄C) 轉為秒數，存於 G3 開始
            ws["G2"] = "MyET秒數"
            max_row = ws.max_row

            for i in range(3, max_row + 1):
                d_cell = f"D{i}"
                g_cell = f"G{i}"
                ws[g_cell] = (
                    f'=IFERROR(LEFT({d_cell},FIND("小時",{d_cell})-1)*3600,0) + '
                    f'IFERROR(MID({d_cell},FIND("小時",{d_cell})+2,FIND("分鐘",{d_cell})-FIND("小時",{d_cell})-2)*60,0)'
                )



            wb.save(output_path)
            

        else:
            # EasyTest csv 處理邏輯
            # CSV 處理邏輯從 app2.py 移植過來
            try:
                df = pd.read_csv(input_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(input_path, encoding='big5')
                except UnicodeDecodeError:
                    df = pd.read_csv(input_path, encoding='ISO-8859-1')

            if '總時數' in df.columns:
                df['總時數'] = df['總時數'].astype(str)
            if '登入次數' in df.columns:
                df = df.drop(columns=['登入次數'])

            df.to_excel(output_path, index=False)
            wb = load_workbook(output_path)
            ws = wb.active

            # Add formulas
            ws["D1"] = "秒數"
            for i in range(2, len(df) + 2):
                c_cell = f"C{i}"
                d_cell = f"D{i}"
                formula_d = '=IFERROR(LEFT({},FIND("時",{})-1)*3600,0) + IFERROR(MID({},FIND("時",{})+1,FIND("分",{})-FIND("時",{})-1)*60,0)'.format(
                    c_cell, c_cell, c_cell, c_cell, c_cell, c_cell
                )
                ws[d_cell] = formula_d


            wb.save(output_path)

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

@app.route('/new')
def new():
    show_captcha = 'captcha_verified' not in session or not session['captcha_verified']
    return render_template('new.html', show_captcha=show_captcha)

@app.route('/new/upload', methods=['POST'])
def upload_file():
    if 'captcha_verified' in session and session['captcha_verified']:
        pass
    else:
        captcha_token = request.form.get('cf-turnstile-response')
        if not captcha_token:
            return {"error": "CAPTCHA token is missing"}, 400

        verification_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": TURNSTILE_SECRET_KEY,
            "response": captcha_token,
            "remoteip": request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('HTTP_X_REAL_IP', request.environ.get('REMOTE_ADDR')))
        }
        response = requests.post(verification_url, data=payload)
        result = response.json()

        if not result.get("success"):
            return {"error": "CAPTCHA validation failed"}, 403

        # Set the flag
        session['captcha_verified'] = True
        session.permanent = True

    # Check if both files are present
    if 'history_file' not in request.files or 'online_info_file' not in request.files:
        return "請上傳 history*.csv 和 OnlineInfo_*.xlsx 檔案", 400

    history_file = request.files['history_file']
    online_info_file = request.files['online_info_file']

    if history_file.filename == '' or online_info_file.filename == '':
        return "沒有檔案被選取", 400

    # Validate file extensions
    if not history_file.filename.lower().endswith('.csv'):
        return "History 檔案必須是 .csv 格式", 400

    if not online_info_file.filename.lower().endswith('.xlsx'):
        return "OnlineInfo 檔案必須是 .xlsx 格式", 400

    try:
        # Secure and save uploaded files
        history_filename = secure_filename(history_file.filename)
        online_info_filename = secure_filename(online_info_file.filename)
        history_path = os.path.join(UPLOAD_FOLDER, history_filename)
        online_info_path = os.path.join(UPLOAD_FOLDER, online_info_filename)
        history_file.save(history_path)
        online_info_file.save(online_info_path)
    
        # Load history*.csv
        try:
            history_df = pd.read_csv(history_path, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                history_df = pd.read_csv(history_path, encoding='big5')
            except UnicodeDecodeError:
                history_df = pd.read_csv(history_path, encoding='ISO-8859-1')
    
        required_history_columns = ["使用者帳號", "總時數"]
        for col in required_history_columns:
            if col not in history_df.columns:
                return f"History 檔案缺少必要的欄位: {col}", 400
    
        # 只保留需要的欄位
        history_df = history_df[["使用者帳號", "總時數"]]
        history_df['總時數'] = history_df['總時數'].astype(str)  # 確保總時數為字串格式
    
        # Process based on file type
        if online_info_filename.endswith("Stud_List.xlsx"):
            # Process *_Stud_List.xlsx
            stud_df = pd.read_excel(
                online_info_path,
                sheet_name=0,
                skiprows=4,  # 跳過 A1:D4，A5 作為標題
                usecols=[0, 1, 2, 3],  # A-D 欄 (索引 0-3)
                names=["班級", "學號", "姓名", "修別"]  # 自訂標題名稱
            )
            stud_df = stud_df.dropna(subset=["學號"])  # 移除學號為空的行
    
            # Merge with history_df using left join (stud_df as base table)
            merged_df = pd.merge(
                stud_df,
                history_df[["使用者帳號", "總時數"]],
                left_on="學號",
                right_on="使用者帳號",
                how="left"
            )
    
            # Select and prepare result dataframe
            result_df = merged_df[["班級", "學號", "姓名", "修別", "總時數"]].copy()
            result_df.columns = ["班級", "學號", "姓名", "修別", "EasyTest總時數"]  # 重命名為輸出標題
            result_df.insert(5, "EasyTest秒數", "")  # 插入空白欄位
            result_df.insert(6, "成績", "")  # 插入空白欄位
    
            # Save to result file
            result_filename = 'result_stud_list.xlsx'
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            result_df.to_excel(result_path, index=False, startrow=4)  # 從第 5 行開始寫入
    
            # Use openpyxl to adjust headers and add formulas
            wb = load_workbook(result_path)
            ws = wb.active
    
            # Write headers at row 5 (A5:G5)
            ws["A5"] = "班級"
            ws["B5"] = "學號"
            ws["C5"] = "姓名"
            ws["D5"] = "修別"
            ws["E5"] = "EasyTest總時數"
            ws["F5"] = "EasyTest秒數"
            ws["G5"] = "成績"
    
            # Preserve "EasyTest總時數" as text in E6:E{max_row}
            max_row = ws.max_row
            for i in range(6, max_row + 1):
                total_time = ws[f"E{i}"].value
                if total_time is not None:
                    ws[f"E{i}"] = f"{total_time}"  # 儲存為文字
    
            # Add "EasyTest秒數" formula in F6:F{max_row}
            for i in range(6, max_row + 1):
                total_seconds = f"E{i}"
                formula_f = (
                    f'=IFERROR(LEFT({total_seconds},FIND("時",{total_seconds})-1)*3600,0) + '
                    f'IFERROR(MID({total_seconds},FIND("時",{total_seconds})+1,FIND("分",{total_seconds})-FIND("時",{total_seconds})-1)*60,0)'
                )
                ws[f"F{i}"] = formula_f
    
            # Add "成績" formula in G6:G{max_row}
            for i in range(6, max_row + 1):
                seconds_cell = f"F{i}"
                formula_g = (
                    f'=IF({seconds_cell}>=72000,10,IF({seconds_cell}>0,{seconds_cell}/72000*10,0))'
                )
                ws[f"G{i}"] = formula_g
    
            # 刪除前 4 列 (A1:G4)
            ws.delete_rows(1, 4)  # 從第 1 行開始刪除 4 行
    
            wb.save(result_path)
        
        elif online_info_file.filename.startswith("ScoreReport_"):
            # Process ScoreReport_*.xlsx
            online_df = pd.read_excel(
                online_info_path,
                sheet_name=0,
                skiprows=1,  # Assuming headers are in the second row (A2)
                usecols=["帳號", "名字", "上線時間", "平均分數", "次"]
            )
            try:
                history_df = pd.read_csv(history_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    history_df = pd.read_csv(history_path, encoding='big5')
                except UnicodeDecodeError:
                    history_df = pd.read_csv(history_path, encoding='ISO-8859-1')

            required_history_columns = ["使用者帳號", "姓名", "登入次數", "總時數"]
            for col in required_history_columns:
                if col not in history_df.columns:
                    return f"History 檔案缺少必要的欄位: {col}", 400

            history_df['總時數'] = history_df['總時數'].astype(str)
            history_df = history_df.drop(columns=['登入次數'])

            merged_df = pd.merge(
                online_df,
                history_df,
                left_on='帳號',
                right_on='使用者帳號',
                how='left',
                suffixes=('_online', '_history')
            )

            if '名字' not in merged_df.columns:
                return "合併後的資料缺少 '名字' 欄位", 400
            if '總時數' not in merged_df.columns:
                return "合併後的資料缺少 '總時數' 欄位", 400

            result_df = merged_df[["帳號","名字","上線時間","總時數"]].copy()

            result_filename = 'result.xlsx'
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            result_df.to_excel(result_path, index=False)

            wb = load_workbook(result_path)
            ws = wb.active
            max_row = ws.max_row

            # EasyTest總時數 in D2:D{max_row}
            ws["D1"] = "EasyTest總時數"
            for i in range(2, max_row + 1):
                total_time = ws[f"D{i}"].value
                if total_time is not None:
                    ws[f"D{i}"].value = f"{total_time}"  # Prepend apostrophe to store as text

            # MyET秒數 in E2:E{max_row}
            ws["E1"] = "MyET秒數"
            for i in range(2, max_row + 1):
                time_cell = f"C{i}"  # 上線時間在第 3 欄
                ws[f"E{i}"] = (
                    f'=IFERROR(LEFT({time_cell},FIND("小時",{time_cell})-1)*3600,0) + '
                    f'IFERROR(MID({time_cell},FIND("小時",{time_cell})+2,FIND("分鐘",{time_cell})-FIND("小時",{time_cell})-2)*60,0)'
                )

            # EasyTest秒數 in F2:F{max_row}
            ws["F1"] = "EasyTest秒數"
            for i in range(2, max_row + 1):
                total_seconds = f"D{i}"  # '總時數' 在 D 欄
                formula_f = (
                    f'=IFERROR(LEFT({total_seconds},FIND("時",{total_seconds})-1)*3600,0) + '
                    f'IFERROR(MID({total_seconds},FIND("時",{total_seconds})+1,FIND("分",{total_seconds})-FIND("時",{total_seconds})-1)*60,0)'
                )
                ws[f"F{i}"] = formula_f

            wb.save(result_path)

        elif online_info_file.filename.startswith("OnlineInfo"):
            # Process OnlineInfo_*.xlsx

            online_df = pd.read_excel(
                online_info_path,
                sheet_name=0,
                skiprows=1,  # Assuming headers are in the second row (A2)
                usecols=["帳號", "姓名", "總上線時間", "登入學習次數"]
            )

            # Process history*.csv
            try:
                history_df = pd.read_csv(history_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    history_df = pd.read_csv(history_path, encoding='big5')
                except UnicodeDecodeError:
                    history_df = pd.read_csv(history_path, encoding='ISO-8859-1')

            # Ensure necessary columns exist
            required_history_columns = ["使用者帳號", "姓名", "登入次數", "總時數"]
            for col in required_history_columns:
                if col not in history_df.columns:
                    return f"History 檔案缺少必要的欄位: {col}", 400

            # Convert '總時數' to string
            history_df['總時數'] = history_df['總時數'].astype(str)

            # Drop '登入次數' column
            history_df = history_df.drop(columns=['登入次數'])

            # Merge datasets based on account numbers with suffixes to handle duplicate '姓名'
            merged_df = pd.merge(
                online_df,
                history_df,
                left_on='帳號',
                right_on='使用者帳號',
                how='left',
                suffixes=('_online', '_history')
            )

            # Check if '姓名_online' exists
            if '姓名_online' not in merged_df.columns:
                return "合併後的資料缺少 '姓名_online' 欄位", 400

            # Select and rename necessary columns
            result_df = merged_df[
                ['帳號', '姓名_online', '總上線時間', '登入學習次數', '總時數']
            ].copy()
            result_df.rename(columns={'姓名_online': '姓名'}, inplace=True)

            # Insert blank columns for MyET calculations to position '總時數' in H
            result_df.insert(4, 'MyET秒數', '')
            result_df.insert(5, 'MyET時分', '')
            # '總時數' will now be in H (8th column)

            # Save merged data to Excel
            result_filename = 'result.xlsx'
            result_path = os.path.join(RESULT_FOLDER, result_filename)
            result_df.to_excel(result_path, index=False)

            # Use openpyxl to add formulas
            wb = load_workbook(result_path)
            ws = wb.active

            max_row = ws.max_row

            # Add "MyET秒數" formula in E2:E{max_row}
            ws["E1"] = "MyET秒數"
            for i in range(2, max_row + 1):
                total_time_cell = f"C{i}"  # 總上線時間在 C 欄
                formula_e = (
                    f'=IFERROR(LEFT({total_time_cell},FIND("天",{total_time_cell})-1)*86400,0) + '
                    f'IFERROR(MID({total_time_cell},FIND("天",{total_time_cell})+2,FIND("小時",{total_time_cell})-FIND("天",{total_time_cell})-2)*3600,0) + '
                    f'IFERROR(MID({total_time_cell},FIND("小時",{total_time_cell})+2,FIND("分",{total_time_cell})-FIND("小時",{total_time_cell})-2)*60,0) + '
                    f'IFERROR(MID({total_time_cell},FIND("分",{total_time_cell})+2,FIND("秒",{total_time_cell})-FIND("分",{total_time_cell})-2),0)'
                )
                ws[f"E{i}"] = formula_e

            # Add "MyET時分" formula in F2:F{max_row}
            ws["F1"] = "MyET時分"
            for i in range(2, max_row + 1):
                myet_seconds = f"E{i}"
                formula_f = (
                    f'=TEXT(INT({myet_seconds}/3600),"00")&"時"&'
                    f'TEXT(INT(MOD({myet_seconds},3600)/60),"00")&"分"'
                )
                ws[f"F{i}"] = formula_f

            # '總時數' 已經在 G 欄，確保以文字形式儲存
            ws["G1"] = "EasyTest總時數"
            for i in range(2, max_row + 1):
                total_time = ws[f"G{i}"].value
                if total_time is not None:
                    ws[f"G{i}"] = f"{total_time}"  # Prepend apostrophe to store as text

            # Add "EasyTest秒數" formula in H2:H{max_row}
            ws["H1"] = "EasyTest秒數"
            for i in range(2, max_row + 1):
                total_seconds = f"G{i}"  # '總時數' 在 G 欄
                formula_h = (
                    f'=IFERROR(LEFT({total_seconds},FIND("時",{total_seconds})-1)*3600,0) + '
                    f'IFERROR(MID({total_seconds},FIND("時",{total_seconds})+1,FIND("分",{total_seconds})-FIND("時",{total_seconds})-1)*60,0)'
                )
                ws[f"H{i}"] = formula_h

            wb.save(result_path)
            pass
        else:
            return "不支援的檔案格式", 400

        # Clean up uploaded files
        try:
            os.remove(history_path)
            os.remove(online_info_path)
            print("已成功刪除上傳的檔案。")
        except Exception as e:
            print(f"刪除檔案時發生錯誤: {str(e)}")

        @after_this_request
        def remove_result_file(response):
            try:
                os.remove(result_path)
                print(f"已成功刪除結果檔案: {result_path}")
            except Exception as e:
                print(f"刪除結果檔案時發生錯誤: {str(e)}")
            return response

        return send_file(result_path, as_attachment=True)

    except Exception as e:
        return f"處理檔案時發生錯誤: {str(e)}", 500

if __name__ == '__main__':
    cleanup_thread = Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
