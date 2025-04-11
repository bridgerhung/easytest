
import pandas as pd
from utils.time_parser import parse_time_to_seconds, parse_myet_time_to_seconds, seconds_to_hour_minute, seconds_to_score

def process_online_info(df_online, df_history):
    df_online["MyET秒數"] = df_online["總上線時間"].apply(parse_myet_time_to_seconds)
    df_online["MyET時分"] = df_online["MyET秒數"].apply(seconds_to_hour_minute)

    df_history["EasyTest總時數"] = df_history["總時數"].astype(str)
    if "登入次數" in df_history.columns:
        df_history = df_history.drop(columns=["登入次數"])

    merged = pd.merge(
        df_online,
        df_history,
        left_on="帳號",
        right_on="使用者帳號",
        how="left",
        suffixes=("_online", "_history")
    )

    merged.rename(columns={"姓名_online": "姓名"}, inplace=True)
    merged["EasyTest秒數"] = merged["EasyTest總時數"].apply(parse_time_to_seconds)

    result_df = merged[[
        '帳號', '姓名', '總上線時間', '登入學習次數',
        'MyET秒數', 'MyET時分', '總時數', 'EasyTest秒數'
    ]]

    return result_df

def process_score_report(df_score, df_history):
    df_score["MyET秒數"] = df_score["上線時間"].apply(parse_myet_time_to_seconds)

    df_history["EasyTest總時數"] = df_history["總時數"].astype(str)
    if "登入次數" in df_history.columns:
        df_history = df_history.drop(columns=["登入次數"])

    merged = pd.merge(
        df_score,
        df_history,
        left_on="帳號",
        right_on="使用者帳號",
        how="left",
        suffixes=("_online", "_history")
    )

    merged.rename(columns={"姓名_online": "姓名"}, inplace=True)
    merged["EasyTest秒數"] = merged["EasyTest總時數"].apply(parse_time_to_seconds)

    result_df = merged[[
        '帳號', '名字', '上線時間', 'MyET秒數', '總時數', 'EasyTest秒數'
    ]]

    return result_df

def process_easytest(df_stud, df_history):
    df_stud = df_stud.dropna(subset=["學號"])
    df_history["EasyTest總時數"] = df_history["總時數"].astype(str)

    merged = pd.merge(
        df_stud,
        df_history[["使用者帳號", "EasyTest總時數"]],
        left_on="學號",
        right_on="使用者帳號",
        how="left"
    )

    result_df = merged[["班級", "學號", "姓名", "修別", "EasyTest總時數"]].copy()
    result_df.columns = ["班級", "學號", "姓名", "修別", "EasyTest總時數"]

    result_df["EasyTest秒數"] = result_df["EasyTest總時數"].apply(parse_time_to_seconds)
    result_df["成績"] = result_df["EasyTest秒數"].apply(seconds_to_score)

    return result_df
