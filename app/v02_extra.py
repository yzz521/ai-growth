from .db import db

def ensure_v02_extra_schema():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS content_generation_context (
          content_id TEXT PRIMARY KEY,
          brand_id TEXT,
          audience_id TEXT,
          strategy_id TEXT,
          prompt_versions_json TEXT NOT NULL DEFAULT '{}',
          config_snapshot_json TEXT NOT NULL DEFAULT '{}',
          created_at TEXT NOT NULL,
          FOREIGN KEY(content_id) REFERENCES content_drafts(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_content_context_brand ON content_generation_context(brand_id);
        """)
