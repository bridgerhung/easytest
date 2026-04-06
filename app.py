from flask import Flask, request, send_file, session, render_template, after_this_request
import os
import time
import csv
import zipfile
import uuid
import hashlib
import logging
import pandas as pd
import requests
from threading import Thread, Timer
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from config import (
    UPLOAD_FOLDER,
    RESULT_FOLDER,
    SECRET_KEY,
    SESSION_LIFETIME,
    TURNSTILE_SECRET_KEY,
    TURNSTILE_SITE_KEY,
    MAX_CONTENT_LENGTH,
    DEBUG,
    CAPTCHA_VERIFIED_TTL,
)
from utils.file_ops import delete_old_files
from services.processor import process_combined

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_LIFETIME
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def cleanup_task():
    while True:
        delete_old_files(UPLOAD_FOLDER, 60)
        delete_old_files(RESULT_FOLDER, 60)
        time.sleep(60)


def _schedule_delete(path, delay_seconds=120):
    def _delete():
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError as exc:
            logger.warning("Failed to delete file %s: %s", path, exc)

    Timer(delay_seconds, _delete).start()


def _build_unique_filename(original_filename, prefix):
    _, ext = os.path.splitext(secure_filename(original_filename))
    unique_id = uuid.uuid4().hex
    return f"{prefix}_{unique_id}{ext.lower()}"


def _build_client_fingerprint():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    client_ip = forwarded_for.split(",", 1)[0].strip() if forwarded_for else (request.remote_addr or "")
    user_agent = request.headers.get("User-Agent", "")
    raw = f"{client_ip}|{user_agent}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_captcha_verified_for_request():
    verified_data = session.get("captcha_verified")
    if not isinstance(verified_data, dict):
        return False

    verified_at = verified_data.get("verified_at")
    fingerprint = verified_data.get("fingerprint")
    if verified_at is None or not fingerprint:
        return False

    try:
        verified_at = float(verified_at)
    except (TypeError, ValueError):
        return False

    if time.time() - verified_at > CAPTCHA_VERIFIED_TTL:
        return False

    return fingerprint == _build_client_fingerprint()


def _read_csv_with_fallback(path):
    decode_strategies = [
        ("utf-8-sig", "strict"),
        ("utf-8", "strict"),
        ("cp950", "strict"),
        ("big5", "strict"),
        ("cp950", "replace"),
        ("big5", "replace"),
        ("utf-16", "strict"),
        ("ISO-8859-1", "strict"),
    ]

    for encoding, encoding_errors in decode_strategies:
        try:
            return pd.read_csv(
                path,
                encoding=encoding,
                encoding_errors=encoding_errors,
                sep=None,
                engine="python",
            )
        except TypeError:
            # Older pandas may not support `encoding_errors`; keep behavior compatible.
            try:
                return pd.read_csv(path, encoding=encoding, sep=None, engine="python")
            except UnicodeDecodeError:
                continue
        except UnicodeDecodeError:
            continue
    raise ValueError("CSV 編碼無法辨識，請確認檔案內容是否為有效 CSV。")


def _normalize_column_name(name):
    # Normalize BOM/whitespace variants so uploaded files from different tools can still match expected headers.
    return "".join(str(name).replace("\ufeff", "").replace("\u200b", "").strip().split())


def _read_excel_with_required_columns(path, *, skiprows, required_columns, sheet_name=0):
    df = pd.read_excel(path, sheet_name=sheet_name, skiprows=skiprows)
    raw_columns = [str(col).strip() for col in df.columns]
    normalized_map = {"".join(col.split()): col for col in raw_columns}

    selected_columns = []
    for required in required_columns:
        normalized_required = "".join(required.split())
        matched = normalized_map.get(normalized_required)
        if matched:
            selected_columns.append(matched)

    missing = [
        required
        for required in required_columns
        if "".join(required.split()) not in normalized_map
    ]
    if missing:
        raise ValueError(f"欄位缺少: {', '.join(missing)}")

    output = df[selected_columns].copy()
    output.columns = required_columns
    return output


def _validate_csv_content(path):
    for encoding in ("utf-8", "big5", "ISO-8859-1"):
        try:
            with open(path, "r", encoding=encoding, errors="strict") as f:
                sample = f.read(8192)
        except UnicodeDecodeError:
            continue

        if not sample.strip():
            raise ValueError("CSV 檔案是空的，請重新匯出後再上傳。")

        try:
            csv.Sniffer().sniff(sample)
            return
        except csv.Error:
            # Fallback heuristic for common delimited text.
            if any(delimiter in sample for delimiter in [",", "\t", ";"]) and "\n" in sample:
                return

    raise ValueError("檔案內容不是有效的 CSV 格式，請確認檔案沒有損毀。")


def _validate_xlsx_content(path):
    if not zipfile.is_zipfile(path):
        raise ValueError("檔案內容不是有效的 XLSX 格式，請確認檔案沒有損毀。")

    with zipfile.ZipFile(path, "r") as zf:
        names = set(zf.namelist())
        if "[Content_Types].xml" not in names or not any(name.startswith("xl/") for name in names):
            raise ValueError("檔案內容不是有效的 XLSX 格式，請重新匯出後再上傳。")


def _validate_uploaded_content(path, expected_type):
    if expected_type == "csv":
        _validate_csv_content(path)
        return
    if expected_type == "xlsx":
        _validate_xlsx_content(path)
        return
    raise ValueError(f"不支援的檔案驗證類型: {expected_type}")


def _verify_captcha_if_needed():
    if _is_captcha_verified_for_request():
        return None

    captcha_token = request.form.get('cf-turnstile-response')
    if not captcha_token:
        return {"error": "CAPTCHA token is missing"}, 400

    if not TURNSTILE_SECRET_KEY:
        logger.error("TURNSTILE_SECRET_KEY is not configured.")
        return {"error": "CAPTCHA service is not configured"}, 500

    verification_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {
        "secret": TURNSTILE_SECRET_KEY,
        "response": captcha_token,
        "remoteip": request.remote_addr
    }

    try:
        response = requests.post(verification_url, data=payload, timeout=10)
        result = response.json()
    except requests.RequestException as exc:
        logger.warning("CAPTCHA verification request failed: %s", exc)
        return {"error": "CAPTCHA validation failed"}, 502

    if not result.get("success"):
        return {"error": "CAPTCHA validation failed"}, 403

    session['captcha_verified'] = {
        "verified_at": time.time(),
        "fingerprint": _build_client_fingerprint(),
    }
    session.permanent = True
    return None


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(_error):
    max_mb = app.config['MAX_CONTENT_LENGTH'] // (1024 * 1024)
    return {"error": f"檔案過大，請上傳小於 {max_mb}MB 的檔案"}, 413

@app.route('/')
def home():
    show_captcha = not _is_captcha_verified_for_request()
    return render_template('new.html', show_captcha=show_captcha, turnstile_site_key=TURNSTILE_SITE_KEY)


def _read_easytest_df(path):
    history_df = _read_csv_with_fallback(path)
    history_df = history_df.astype(str)
    required_history_cols = ["使用者帳號", "總時數"]
    normalized_map = {
        _normalize_column_name(col): col
        for col in history_df.columns
    }

    selected_columns = []
    missing_history_cols = []
    for required in required_history_cols:
        matched = normalized_map.get(_normalize_column_name(required))
        if matched:
            selected_columns.append(matched)
        else:
            missing_history_cols.append(required)

    if missing_history_cols:
        existing = ", ".join(str(col) for col in history_df.columns)
        raise ValueError(
            f"EasyTest 檔案欄位缺少: {', '.join(missing_history_cols)}。"
            f"目前讀到欄位: {existing}。"
            "請確認 CSV 第一列標題包含「使用者帳號」與「總時數」。"
        )

    output = history_df[selected_columns].copy()
    output.columns = required_history_cols
    return output


def _read_myet_df(path, filename):
    if filename.startswith("OnlineInfo"):
        return _read_excel_with_required_columns(
            path,
            sheet_name=0,
            skiprows=1,
            required_columns=["帳號", "姓名", "總上線時間"],
        )

    if filename.startswith("ScoreReport"):
        return _read_excel_with_required_columns(
            path,
            sheet_name=0,
            skiprows=1,
            required_columns=["帳號", "名字", "上線時間"],
        )

    try:
        return _read_excel_with_required_columns(
            path,
            sheet_name=0,
            skiprows=1,
            required_columns=["帳號", "姓名", "總上線時間"],
        )
    except ValueError:
        return _read_excel_with_required_columns(
            path,
            sheet_name=0,
            skiprows=1,
            required_columns=["帳號", "名字", "上線時間"],
        )


def _read_student_df(path):
    try:
        stud_df = pd.read_excel(
            path,
            sheet_name=0,
            skiprows=4,
            usecols=[0, 1, 2, 3],
            names=["班級", "學號", "姓名", "修別"],
        )
        return stud_df[["學號", "姓名"]]
    except Exception:
        fallback_df = pd.read_excel(path, sheet_name=0)
        fallback_df.columns = [str(col).strip() for col in fallback_df.columns]
        required_cols = ["學號", "姓名"]
        missing = [col for col in required_cols if col not in fallback_df.columns]
        if missing:
            raise ValueError(f"學生資料表欄位缺少: {', '.join(missing)}")
        return fallback_df[["學號", "姓名"]]


@app.route('/upload', methods=['POST'])
def upload_file():
    captcha_check = _verify_captcha_if_needed()
    if captcha_check:
        return captcha_check

    easytest_file = request.files.get('easytest_file')
    myet_file = request.files.get('myet_file')
    student_list_file = request.files.get('student_list_file')

    has_easytest = bool(easytest_file and easytest_file.filename)
    has_myet = bool(myet_file and myet_file.filename)
    has_student = bool(student_list_file and student_list_file.filename)

    if not (has_easytest or has_myet or has_student):
        return {"error": "請至少上傳 EasyTest 或 MyET 檔案"}, 400

    if has_student and not (has_easytest or has_myet):
        return {"error": "不可以只上傳學生資料表，請至少再上傳 EasyTest 或 MyET 檔案"}, 400

    if has_easytest and not easytest_file.filename.lower().endswith('.csv'):
        return {"error": "EasyTest 檔案必須是 .csv 格式"}, 400

    if has_myet and not myet_file.filename.lower().endswith('.xlsx'):
        return {"error": "MyET 檔案必須是 .xlsx 格式"}, 400

    if has_student and not student_list_file.filename.lower().endswith('.xlsx'):
        return {"error": "學生資料表檔案必須是 .xlsx 格式"}, 400

    easytest_path = None
    myet_path = None
    student_list_path = None
    result_path = None

    try:
        easytest_df = None
        myet_df = None
        student_df = None

        if has_easytest:
            easytest_path = os.path.join(UPLOAD_FOLDER, _build_unique_filename(easytest_file.filename, "easytest"))
            easytest_file.save(easytest_path)
            _validate_uploaded_content(easytest_path, "csv")
            easytest_df = _read_easytest_df(easytest_path)

        if has_myet:
            myet_path = os.path.join(UPLOAD_FOLDER, _build_unique_filename(myet_file.filename, "myet"))
            myet_file.save(myet_path)
            _validate_uploaded_content(myet_path, "xlsx")
            myet_df = _read_myet_df(myet_path, myet_file.filename)

        if has_student:
            student_list_path = os.path.join(UPLOAD_FOLDER, _build_unique_filename(student_list_file.filename, "student_list"))
            student_list_file.save(student_list_path)
            _validate_uploaded_content(student_list_path, "xlsx")
            student_df = _read_student_df(student_list_path)

        result_df = process_combined(easytest_df, myet_df, student_df)

        download_filename = "result.xlsx"
        result_storage_name = _build_unique_filename(download_filename, "result")
        result_path = os.path.join(RESULT_FOLDER, result_storage_name)
        result_df.to_excel(result_path, index=False)

        @after_this_request
        def cleanup(response):
            for path in (easytest_path, myet_path, student_list_path, result_path):
                if path:
                    _schedule_delete(path)
            return response

        return send_file(result_path, as_attachment=True, download_name=download_filename)

    except ValueError as e:
        for path in (easytest_path, myet_path, student_list_path, result_path):
            if path and os.path.exists(path):
                _schedule_delete(path, delay_seconds=1)
        logger.info("Upload validation failed: %s", e)
        return {"error": str(e)}, 400
    except Exception as e:
        for path in (easytest_path, myet_path, student_list_path, result_path):
            if path and os.path.exists(path):
                _schedule_delete(path, delay_seconds=1)
        logger.exception("Upload processing failed")
        return {"error": f"處理檔案時發生錯誤: {str(e)}"}, 500

if __name__ == '__main__':
    cleanup_thread = Thread(target=cleanup_task, daemon=True)
    cleanup_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)