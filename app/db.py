import json, sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from .config import DB_PATH, ensure_dirs

def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def dump(v): return json.dumps(v, ensure_ascii=False)
def load(v, default=None):
    try: return json.loads(v) if v else ([] if default is None else default)
    except (ValueError, TypeError): return [] if default is None else default
@contextmanager
def db():
    ensure_dirs(); c=sqlite3.connect(DB_PATH, timeout=20); c.row_factory=sqlite3.Row
    c.execute('PRAGMA foreign_keys=ON'); c.execute('PRAGMA journal_mode=WAL')
    try: yield c; c.commit()
    except Exception: c.rollback(); raise
    finally: c.close()
def init_db():
    with db() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS inbox_items(id TEXT PRIMARY KEY, source_type TEXT NOT NULL, source_name TEXT, title TEXT NOT NULL, raw_text TEXT NOT NULL, summary TEXT, tags_json TEXT NOT NULL DEFAULT '[]', extracted_json TEXT NOT NULL DEFAULT '{}', status TEXT NOT NULL DEFAULT 'PENDING', original_filename TEXT, stored_filename TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS knowledge_entries(id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, summary TEXT, tags_json TEXT NOT NULL DEFAULT '[]', source_inbox_id TEXT, source_type TEXT, source_ref TEXT, status TEXT NOT NULL DEFAULT 'ACTIVE', current_version INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(source_inbox_id) REFERENCES inbox_items(id) ON DELETE SET NULL);
        CREATE TABLE IF NOT EXISTS knowledge_versions(id TEXT PRIMARY KEY, knowledge_id TEXT NOT NULL, version_no INTEGER NOT NULL, content TEXT NOT NULL, summary TEXT, change_reason TEXT, created_at TEXT NOT NULL, UNIQUE(knowledge_id,version_no), FOREIGN KEY(knowledge_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS content_drafts(id TEXT PRIMARY KEY, topic TEXT NOT NULL, platform TEXT NOT NULL, audience TEXT, tone TEXT, title TEXT NOT NULL, body TEXT NOT NULL, source_knowledge_ids_json TEXT NOT NULL DEFAULT '[]', status TEXT NOT NULL DEFAULT 'DRAFT', generated_mode TEXT NOT NULL DEFAULT 'local_fallback', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS publish_records(id TEXT PRIMARY KEY, content_id TEXT NOT NULL, platform TEXT NOT NULL, publish_url TEXT, external_post_id TEXT, status TEXT NOT NULL DEFAULT 'PUBLISHED_MANUALLY', published_at TEXT, note TEXT, created_at TEXT NOT NULL, FOREIGN KEY(content_id) REFERENCES content_drafts(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS leads(id TEXT PRIMARY KEY, name TEXT NOT NULL, company TEXT, contact TEXT, source_platform TEXT, source_content_id TEXT, requirement TEXT, budget TEXT, status TEXT NOT NULL DEFAULT 'NEW', notes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(source_content_id) REFERENCES content_drafts(id) ON DELETE SET NULL);
        CREATE INDEX IF NOT EXISTS idx_inbox_status_created ON inbox_items(status,created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_knowledge_updated ON knowledge_entries(updated_at DESC);
        CREATE INDEX IF NOT EXISTS idx_content_status_created ON content_drafts(status,created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_leads_status_created ON leads(status,created_at DESC);
        ''')
        cols={r[1] for r in c.execute('PRAGMA table_info(content_drafts)')}
        if 'generated_mode' not in cols: c.execute("ALTER TABLE content_drafts ADD COLUMN generated_mode TEXT NOT NULL DEFAULT 'local_fallback'")
def row(r):
    if r is None: return None
    d=dict(r)
    for k in ('tags_json','extracted_json','source_knowledge_ids_json'):
        if k in d: d[k.removesuffix('_json')]=load(d.pop(k), {} if k=='extracted_json' else [])
    return d
