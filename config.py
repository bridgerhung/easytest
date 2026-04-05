import os
from datetime import timedelta


def _env_bool(name, default=False):
	value = os.getenv(name)
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY")
TURNSTILE_SITE_KEY = os.getenv("TURNSTILE_SITE_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
SESSION_LIFETIME = timedelta(minutes=60)
CAPTCHA_VERIFIED_TTL = int(os.getenv("CAPTCHA_VERIFIED_TTL", "600"))
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(20 * 1024 * 1024)))
DEBUG = _env_bool("FLASK_DEBUG", default=False)
