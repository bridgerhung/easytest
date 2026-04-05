
import pandas as pd

from utils.time_parser import parse_time_to_seconds, parse_myet_time_to_seconds


OUTPUT_COLUMNS = [
    "學號",
    "姓名",
    "EasyTest 原始資料(Optional)",
    "EasyTest 秒數",
    "MyET原始資料(Optional)",
    "MyET秒數",
]


def _normalize_easytest(df_easytest):
    normalized = df_easytest.copy()
    normalized = normalized.dropna(subset=["使用者帳號"])
    normalized["學號"] = normalized["使用者帳號"].astype(str).str.strip()
    normalized = normalized[normalized["學號"] != ""]

    normalized["EasyTest 原始資料(Optional)"] = (
        normalized["總時數"].fillna("").astype(str).str.strip()
    )
    normalized["EasyTest 秒數"] = normalized["EasyTest 原始資料(Optional)"].apply(
        parse_time_to_seconds
    )

    if "姓名" in normalized.columns:
        normalized["姓名"] = normalized["姓名"].fillna("").astype(str).str.strip()
    else:
        normalized["姓名"] = ""

    return normalized[
        ["學號", "姓名", "EasyTest 原始資料(Optional)", "EasyTest 秒數"]
    ].drop_duplicates(subset=["學號"], keep="first")


def _normalize_myet(df_myet):
    normalized = df_myet.copy()
    normalized = normalized.dropna(subset=["帳號"])
    normalized["學號"] = normalized["帳號"].astype(str).str.strip()
    normalized = normalized[normalized["學號"] != ""]

    if "姓名" not in normalized.columns and "名字" in normalized.columns:
        normalized = normalized.rename(columns={"名字": "姓名"})

    if "姓名" in normalized.columns:
        normalized["姓名"] = normalized["姓名"].fillna("").astype(str).str.strip()
    else:
        normalized["姓名"] = ""

    myet_raw_col = "總上線時間" if "總上線時間" in normalized.columns else "上線時間"
    normalized["MyET原始資料(Optional)"] = (
        normalized[myet_raw_col].fillna("").astype(str).str.strip()
    )
    normalized["MyET秒數"] = normalized["MyET原始資料(Optional)"].apply(
        parse_myet_time_to_seconds
    )

    return normalized[["學號", "姓名", "MyET原始資料(Optional)", "MyET秒數"]].drop_duplicates(
        subset=["學號"], keep="first"
    )


def _normalize_student_list(df_students):
    normalized = df_students.copy()
    normalized = normalized.dropna(subset=["學號"])
    normalized["學號"] = normalized["學號"].astype(str).str.strip()
    normalized = normalized[normalized["學號"] != ""]
    normalized["姓名"] = normalized["姓名"].fillna("").astype(str).str.strip()
    return normalized[["學號", "姓名"]].drop_duplicates(subset=["學號"], keep="first")


def process_combined(df_easytest=None, df_myet=None, df_students=None):
    easytest = _normalize_easytest(df_easytest) if df_easytest is not None else None
    myet = _normalize_myet(df_myet) if df_myet is not None else None
    students = _normalize_student_list(df_students) if df_students is not None else None

    if students is not None:
        base = students.copy()
    else:
        id_frames = []
        if easytest is not None:
            id_frames.append(easytest[["學號"]])
        if myet is not None:
            id_frames.append(myet[["學號"]])

        if not id_frames:
            raise ValueError("至少需要 EasyTest 或 MyET 其中一份資料。")

        base = pd.concat(id_frames, ignore_index=True).drop_duplicates(subset=["學號"])
        base["姓名"] = ""

    result = base.copy()

    if myet is not None:
        result = result.merge(myet, on="學號", how="left", suffixes=("", "_myet"))
        if students is None:
            myet_name = result.get("姓名_myet")
            result["姓名"] = myet_name.where(myet_name.notna(), result["姓名"])
        result = result.drop(columns=["姓名_myet"], errors="ignore")
    else:
        result["MyET原始資料(Optional)"] = ""
        result["MyET秒數"] = 0

    if easytest is not None:
        result = result.merge(easytest, on="學號", how="left", suffixes=("", "_easy"))
        if students is None and myet is None:
            easy_name = result.get("姓名_easy")
            result["姓名"] = easy_name.where(easy_name.notna(), result["姓名"])
        result = result.drop(columns=["姓名_easy"], errors="ignore")
    else:
        result["EasyTest 原始資料(Optional)"] = ""
        result["EasyTest 秒數"] = 0

    for column in OUTPUT_COLUMNS:
        if column not in result.columns:
            result[column] = "" if "原始資料" in column or column == "姓名" else 0

    result["姓名"] = result["姓名"].fillna("").astype(str)
    result["EasyTest 原始資料(Optional)"] = (
        result["EasyTest 原始資料(Optional)"].fillna("").astype(str)
    )
    result["MyET原始資料(Optional)"] = result["MyET原始資料(Optional)"].fillna("").astype(str)
    result["EasyTest 秒數"] = (
        pd.to_numeric(result["EasyTest 秒數"], errors="coerce").fillna(0).astype(int)
    )
    result["MyET秒數"] = pd.to_numeric(result["MyET秒數"], errors="coerce").fillna(0).astype(int)

    result = result[OUTPUT_COLUMNS].sort_values(by=["學號", "姓名"], kind="stable")
    return result.reset_index(drop=True)
