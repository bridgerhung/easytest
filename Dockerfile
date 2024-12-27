# 使用 Python 官方基礎映像
FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件（requirements.txt）到容器中
COPY requirements.txt requirements.txt

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼到容器
COPY . .

# 開放 Flask 默認端口
EXPOSE 5000

# 啟動 Flask 應用
CMD ["/env/bin/gunicorn", "app:app", "-b", "0.0.0.0:5000"]