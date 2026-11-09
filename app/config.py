import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.getenv('AGW_DATA_DIR', ROOT / 'data')).resolve()
UPLOADS = DATA / 'uploads'
DB_PATH = Path(os.getenv('AGW_DB_PATH', DATA / 'app.db')).resolve()
MAX_UPLOAD = int(os.getenv('AGW_MAX_UPLOAD_BYTES', 10 * 1024 * 1024))
MAX_TEXT = int(os.getenv('AGW_MAX_EXTRACTED_CHARS', 100000))
AI_BASE_URL = os.getenv('AI_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
AI_API_KEY = os.getenv('AI_API_KEY', '')
AI_MODEL = os.getenv('AI_MODEL', 'gpt-4o-mini')
AI_TIMEOUT = int(os.getenv('AI_TIMEOUT_SECONDS', '60'))
def ensure_dirs():
    DATA.mkdir(parents=True, exist_ok=True)
    UPLOADS.mkdir(parents=True, exist_ok=True)
    (DATA / 'dropbox').mkdir(parents=True, exist_ok=True)
