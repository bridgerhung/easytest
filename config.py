import os
from datetime import timedelta

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")
SECRET_KEY = '@Your_secret_Key'
SESSION_LIFETIME = timedelta(minutes=60)
