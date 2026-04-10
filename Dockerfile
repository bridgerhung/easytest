# 使用 Python 官方基礎映像
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1

# 設置工作目錄
WORKDIR /app

# 複製依賴文件（requirements.txt）到容器中
COPY requirements.txt requirements.txt

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 建立最小權限使用者
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# 複製應用代碼到容器
COPY . .

# 建立需要寫入的目錄，並收斂權限
RUN mkdir -p /app/uploads /app/results \
	&& chown -R appuser:appgroup /app \
	&& chmod 700 /app/uploads /app/results

USER appuser

# 開放 Flask 默認端口
EXPOSE 5000

# 啟動 Flask 應用
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]