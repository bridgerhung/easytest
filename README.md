# EasyTest & MyET 分數計算服務

上傳 MyET 的 xlsx 檔案 或者 EasyTest 的 csv 檔，
本系統將為您計算成績並轉換為 Excel 檔案。。

使用方式


先建立環境變數（可由 `.env.example` 複製）：

- `SECRET_KEY`
- `TURNSTILE_SECRET_KEY`
- `TURNSTILE_SITE_KEY`
- `MAX_CONTENT_LENGTH`（預設 20971520，約 20MB）


```docker-compose.yml
version: "3.8"

services:
  flask-app:
    image: bridgerhung/easytest:latest
    restart: always
    ports:
      - "5000:5000" # 將容器內的 5000 映射到主機的 5000
    volumes:
      - ./uploads:/app/uploads # 映射上傳文件夾
      - ./results:/app/results # 映射結果文件夾
    # 可選：設置開發模式（移除可避免暴露問題）
```
