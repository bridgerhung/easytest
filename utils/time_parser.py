def parse_time_to_seconds(time_str):
    try:
        if not isinstance(time_str, str):
            return 0
        h = m = 0
        if "時" in time_str:
            h = int(time_str.split("時")[0])
            m = int(time_str.split("時")[1].split("分")[0])
        return h * 3600 + m * 60
    except:
        return 0

def parse_myet_time_to_seconds(time_str):
    try:
        d = h = m = s = 0
        if isinstance(time_str, str):
            parts = time_str.replace('--', '0').replace('－', '0')
            if "天" in parts:
                d = int(parts.split("天")[0].strip())
                parts = parts.split("天")[1]
            if "小時" in parts:
                h = int(parts.split("小時")[0].split()[-1])
            if "分" in parts:
                m = int(parts.split("分")[0].split()[-1])
            if "秒" in parts:
                s = int(parts.split("秒")[0].split()[-1])
        return d * 86400 + h * 3600 + m * 60 + s
    except:
        return 0



def seconds_to_hour_minute(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h:02d}時{m:02d}分"

def seconds_to_score(seconds):
    if seconds >= 72000:
        return 10
    elif seconds > 0:
        return round((seconds / 72000) * 10, 2)
    return 0
