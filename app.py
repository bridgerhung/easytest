from flask import Flask, render_template, request, send_file, after_this_request
import os
import pandas as pd
from openpyxl import load_workbook
from werkzeug.utils import secure_filename
from threading import Thread

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

# Ensure upload and result directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
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
        result_df.insert(5, 'MyET分數', '')
        result_df.insert(6, 'MyET時分', '')
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

        # Add "MyET分數" formula in F2:F{max_row}
        ws["F1"] = "MyET分數"
        for i in range(2, max_row + 1):
            myet_seconds = f"E{i}"
            formula_f = f'=IF({myet_seconds}>=43200, 5, ROUND({myet_seconds}/43200*5, 2))'
            ws[f"F{i}"] = formula_f

        # Add "MyET時分" formula in G2:G{max_row}
        ws["G1"] = "MyET時分"
        for i in range(2, max_row + 1):
            myet_seconds = f"E{i}"
            formula_g = (
                f'=TEXT(INT({myet_seconds}/3600),"00")&"時"&'
                f'TEXT(INT(MOD({myet_seconds},3600)/60),"00")&"分"'
            )
            ws[f"G{i}"] = formula_g

        # '總時數' 已經在 H 欄，確保以文字形式儲存
        ws["H1"] = "EasyTest總時數"
        for i in range(2, max_row + 1):
            total_time = ws[f"H{i}"].value
            if total_time is not None:
                ws[f"H{i}"] = f"{total_time}"  # Prepend apostrophe to store as text

        # Add "EasyTest總時數(Referenced from history.csv 總時數)" in I2:I{max_row}
        ws["I1"] = "EasyTest秒數"
        for i in range(2, max_row + 1):
            total_seconds = f"H{i}"  # '總時數' 在 H 欄
            formula_i = (
                f'=IFERROR(LEFT({total_seconds},FIND("時",{total_seconds})-1)*3600,0) + '
                f'IFERROR(MID({total_seconds},FIND("時",{total_seconds})+1,FIND("分",{total_seconds})-FIND("時",{total_seconds})-1)*60,0)'
            )
            ws[f"I{i}"] = formula_i

        # Add "EasyTest分數" formula in J2:J{max_row}
        ws["J1"] = "EasyTest分數"
        for i in range(2, max_row + 1):
            easytest_seconds = f"I{i}"
            formula_j = f'=IF({easytest_seconds}>=43200, 5, ROUND({easytest_seconds}/43200*5, 2))'
            ws[f"J{i}"] = formula_j
        
        # Add "總分" formula in K2:K{max_row}
            ws["K1"] = "總分"
            for i in range(2, max_row + 1):
                formula_k = f"=F{i} + J{i}"
                ws[f"K{i}"] = formula_k
        

        wb.save(result_path)

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

def cleanup_task():
    while True:
        # Implement any periodic cleanup if necessary
        pass

if __name__ == '__main__':
    # Start cleanup task thread
    cleanup_thread = Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)