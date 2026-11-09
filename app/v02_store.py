import json
import uuid
from .db import db, dump, load, now

TABLES = {
    "brands": ("brand_profiles", {"name","industry","description","products","differentiators","proof_points","voice","cta","prohibited","is_default"}),
    "audiences": ("audience_personas", {"name","segment","pain_points","goals","objections","decision_factors"}),
    "strategies": ("content_strategies", {"name","pillars","ratios","weekly_frequency","goals","enabled"}),
    "platforms": ("platform_content_configs", {"platform","enabled","config"}),
    "prompts": ("prompt_templates", {"code","name","platform","body","active"}),
    "plans": ("content_plans", {"plan_date","topic","platform","goal","status","content_id","notes"}),
    "rules": ("automation_rules", {"name","rule_type","config","enabled","last_run_at","next_run_at"}),
}
JSON_FIELDS = {
    "products","differentiators","proof_points","prohibited","pain_points",
    "goals","objections","decision_factors","pillars","ratios","config"
}
BOOL_FIELDS = {"is_default","enabled","active"}
PLATFORM_DEFAULTS = {
    "xiaohongshu": {"enabled": True, "config": {"format":"图文笔记","title_style":"具体问题 + 明确收益","length":"600-1000字","structure":["痛点场景","解决方法","操作步骤","真实经验","互动问题"],"hashtags":3,"cover":"3:4封面，标题清楚，不夸大"}},
    "douyin": {"enabled": True, "config": {"format":"短视频口播脚本","duration_seconds":60,"structure":["前3秒钩子","问题场景","核心方法","案例或演示","行动引导"],"include_shots":True,"include_subtitles":True}},
    "x": {"enabled": True, "config": {"format":"短帖 / Thread","language":"中文，必要时英文","length":"简洁、观点明确","structure":["观点","论据","结论"],"hashtags":0}},
    "wechat_official": {"enabled": True, "config": {"format":"微信公众号文章","length":"1500-2500字","structure":["标题","引言","背景","分点分析","案例","总结与行动建议"],"include_summary":True}},
}

def uid():
    return str(uuid.uuid4())

def ensure_v02_schema():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS app_preferences (
          key TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS brand_profiles (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, industry TEXT, description TEXT,
          products_json TEXT NOT NULL DEFAULT '[]', differentiators_json TEXT NOT NULL DEFAULT '[]',
          proof_points_json TEXT NOT NULL DEFAULT '[]', voice TEXT, cta TEXT,
          prohibited_json TEXT NOT NULL DEFAULT '[]', is_default INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audience_personas (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, segment TEXT,
          pain_points_json TEXT NOT NULL DEFAULT '[]', goals_json TEXT NOT NULL DEFAULT '[]',
          objections_json TEXT NOT NULL DEFAULT '[]', decision_factors_json TEXT NOT NULL DEFAULT '[]',
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS content_strategies (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, pillars_json TEXT NOT NULL DEFAULT '[]',
          ratios_json TEXT NOT NULL DEFAULT '{}', weekly_frequency INTEGER NOT NULL DEFAULT 5,
          goals_json TEXT NOT NULL DEFAULT '[]', enabled INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS platform_content_configs (
          platform TEXT PRIMARY KEY, enabled INTEGER NOT NULL DEFAULT 1,
          config_json TEXT NOT NULL DEFAULT '{}', updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS prompt_templates (
          id TEXT PRIMARY KEY, code TEXT NOT NULL, name TEXT NOT NULL, platform TEXT,
          body TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1, version INTEGER NOT NULL DEFAULT 1,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS content_plans (
          id TEXT PRIMARY KEY, plan_date TEXT NOT NULL, topic TEXT NOT NULL, platform TEXT NOT NULL,
          goal TEXT, status TEXT NOT NULL DEFAULT 'PLANNED', content_id TEXT, notes TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS automation_rules (
          id TEXT PRIMARY KEY, name TEXT NOT NULL, rule_type TEXT NOT NULL, config_json TEXT NOT NULL DEFAULT '{}',
          enabled INTEGER NOT NULL DEFAULT 0, last_run_at TEXT, next_run_at TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS automation_runs (
          id TEXT PRIMARY KEY, rule_id TEXT, rule_name TEXT NOT NULL, status TEXT NOT NULL,
          started_at TEXT NOT NULL, completed_at TEXT, result_json TEXT, error TEXT
        );
        CREATE TABLE IF NOT EXISTS processing_jobs (
          id TEXT PRIMARY KEY, job_type TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL,
          progress INTEGER NOT NULL DEFAULT 0, result_json TEXT, error TEXT,
          created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_v02_plans_date ON content_plans(plan_date);
        CREATE INDEX IF NOT EXISTS idx_v02_rules_enabled ON automation_rules(enabled,next_run_at);
        CREATE INDEX IF NOT EXISTS idx_v02_jobs_status ON processing_jobs(status,created_at DESC);
        """)
        defaults = {
            "auto_organize": True,
            "auto_promote_knowledge": True,
            "daily_digest_enabled": False,
            "daily_digest_time": "18:00",
            "default_brand_id": None,
            "default_audience_id": None,
            "default_strategy_id": None,
        }
        for key,value in defaults.items():
            c.execute("INSERT OR IGNORE INTO app_preferences(key,value_json,updated_at) VALUES(?,?,?)",(key,dump(value),now()))
        for platform, preset in PLATFORM_DEFAULTS.items():
            c.execute(
                "INSERT OR IGNORE INTO platform_content_configs(platform,enabled,config_json,updated_at) VALUES(?,?,?,?)",
                (platform, int(preset["enabled"]), dump(preset["config"]), now())
            )
        c.execute("INSERT OR IGNORE INTO prompt_templates(id,code,name,platform,body,active,version,created_at,updated_at) VALUES(?,?,?,?,?,1,1,?,?)",
                  ("builtin-content-default","builtin-content-default","通用内容创作规则",None,
                   "先理解品牌定位和目标客户。围绕一个具体问题提供可执行建议；区分事实、观点和推测；不得编造数据、客户案例、用户体验或来源。结尾使用符合本平台习惯的自然行动建议。",now(),now()))

def get_pref(key, default=None):
    with db() as c:
        r=c.execute("SELECT value_json FROM app_preferences WHERE key=?",(key,)).fetchone()
        return load(r["value_json"],default) if r else default

def set_pref(key, value):
    with db() as c:
        c.execute("INSERT INTO app_preferences(key,value_json,updated_at) VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value_json=excluded.value_json,updated_at=excluded.updated_at",(key,dump(value),now()))
    return value

def preferences():
    with db() as c:
        return {r["key"]:load(r["value_json"]) for r in c.execute("SELECT key,value_json FROM app_preferences").fetchall()}

def _decode(kind, record):
    if not record:
        return None
    data=dict(record)
    for field in JSON_FIELDS:
        key=field+"_json"
        if key in data:
            data[field]=load(data.pop(key), {} if field in {"ratios","config"} else [])
    for field in BOOL_FIELDS:
        if field in data:
            data[field]=bool(data[field])
    return data

def list_records(kind, limit=200):
    table, _ = TABLES[kind]
    order = "plan_date ASC" if kind == "plans" else "updated_at DESC"
    with db() as c:
        rows=c.execute(f"SELECT * FROM {table} ORDER BY {order} LIMIT ?",(limit,)).fetchall()
        return [_decode(kind,r) for r in rows]

def get_record(kind, record_id):
    table, _ = TABLES[kind]
    key = "platform" if kind == "platforms" else "id"
    with db() as c:
        return _decode(kind,c.execute(f"SELECT * FROM {table} WHERE {key}=?",(record_id,)).fetchone())

def save_record(kind, payload, record_id=None):
    table, allowed=TABLES[kind]
    data={key:value for key,value in payload.items() if key in allowed}
    if kind=="platforms":
        record_id=str(data.get("platform") or record_id or "")
        if not record_id: raise ValueError("platform 必填")
        data["platform"]=record_id
    else:
        record_id=record_id or uid()
    if kind in {"brands","audiences","strategies"} and not data.get("name"):
        raise ValueError("名称必填")
    if kind=="prompts" and (not data.get("code") or not data.get("name") or not data.get("body")):
        raise ValueError("提示词 code、名称和正文必填")
    if kind=="plans" and not all(data.get(x) for x in ("plan_date","topic","platform")):
        raise ValueError("计划日期、主题和平台必填")
    if kind=="rules" and not all(data.get(x) for x in ("name","rule_type")):
        raise ValueError("规则名称和类型必填")
    t=now()
    row_data={"id":record_id,"created_at":t,"updated_at":t}
    row_data.update(data)
    if kind=="platforms":
        with db() as c:
            c.execute("""INSERT INTO platform_content_configs(platform,enabled,config_json,updated_at)
                         VALUES(?,?,?,?) ON CONFLICT(platform) DO UPDATE SET
                         enabled=excluded.enabled,config_json=excluded.config_json,updated_at=excluded.updated_at""",
                      (record_id,int(bool(data.get("enabled",True))),dump(data.get("config",{})),t))
            return _decode(kind,c.execute("SELECT * FROM platform_content_configs WHERE platform=?",(record_id,)).fetchone())
    if kind=="prompts":
        with db() as c:
            old=c.execute("SELECT version FROM prompt_templates WHERE id=?",(record_id,)).fetchone()
            row_data["version"]=(old["version"]+1) if old else int(data.get("version",1))
            if old:
                row_data.pop("created_at",None)
            row_data.setdefault("active",True)
            row_data["active"]=int(bool(row_data["active"]))
            row_data["version"]=int(row_data["version"])
            cols=list(row_data)
            if old:
                mutable=[x for x in cols if x not in {"id","created_at"}]
                c.execute(f"UPDATE {table} SET "+",".join(f"{x}=?" for x in mutable)+" WHERE id=?",
                          tuple(row_data[x] for x in mutable)+(record_id,))
            else:
                c.execute(f"INSERT INTO {table}("+",".join(cols)+") VALUES("+",".join("?" for _ in cols)+")",tuple(row_data[x] for x in cols))
            return _decode(kind,c.execute("SELECT * FROM prompt_templates WHERE id=?",(record_id,)).fetchone())
    if kind=="rules":
        row_data["config_json"]=dump(data.get("config",{}))
        row_data.pop("config",None)
    cols=[]
    vals=[]
    for field,value in row_data.items():
        if field in JSON_FIELDS:
            col=field+"_json"
            value=dump(value)
        else:
            col=field
        if field in BOOL_FIELDS:
            value=int(bool(value))
        cols.append(col); vals.append(value)
    with db() as c:
        if c.execute(f"SELECT 1 FROM {table} WHERE id=?",(record_id,)).fetchone():
            mutable=[col for col in cols if col not in {"id","created_at"}]
            values=[vals[cols.index(col)] for col in mutable]
            c.execute(f"UPDATE {table} SET "+",".join(f"{col}=?" for col in mutable)+" WHERE id=?",tuple(values)+(record_id,))
        else:
            c.execute(f"INSERT INTO {table}("+",".join(cols)+") VALUES("+",".join("?" for _ in cols)+")",vals)
        return _decode(kind,c.execute(f"SELECT * FROM {table} WHERE id=?",(record_id,)).fetchone())

def delete_record(kind, record_id):
    table,_=TABLES[kind]
    key="platform" if kind=="platforms" else "id"
    with db() as c:
        return c.execute(f"DELETE FROM {table} WHERE {key}=?",(record_id,)).rowcount>0

def create_job(job_type,title):
    job_id=uid(); t=now()
    with db() as c:
        c.execute("INSERT INTO processing_jobs(id,job_type,title,status,progress,created_at,updated_at) VALUES(?,?,?,'PENDING',0,?,?)",(job_id,job_type,title,t,t))
    return job_id

def update_job(job_id,status,progress=0,result=None,error=None):
    with db() as c:
        c.execute("UPDATE processing_jobs SET status=?,progress=?,result_json=?,error=?,updated_at=? WHERE id=?",
                  (status,progress,dump(result) if result is not None else None,error,now(),job_id))

def list_jobs(limit=50):
    with db() as c:
        return [dict(r,result=load(r["result_json"],{})) for r in c.execute("SELECT * FROM processing_jobs ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()]

def create_run(rule_id, rule_name):
    run_id=uid()
    with db() as c:
        c.execute("INSERT INTO automation_runs(id,rule_id,rule_name,status,started_at) VALUES(?,?,?,'RUNNING',?)",(run_id,rule_id,rule_name,now()))
    return run_id

def finish_run(run_id,status,result=None,error=None):
    with db() as c:
        c.execute("UPDATE automation_runs SET status=?,completed_at=?,result_json=?,error=? WHERE id=?",
                  (status,now(),dump(result) if result is not None else None,error,run_id))

def list_runs(limit=50):
    with db() as c:
        return [dict(r,result=load(r["result_json"],{})) for r in c.execute("SELECT * FROM automation_runs ORDER BY started_at DESC LIMIT ?",(limit,)).fetchall()]

def schedule_rule(rule_id,interval_hours=24):
    from datetime import datetime, timedelta, timezone
    next_run=(datetime.now(timezone.utc)+timedelta(hours=max(1,int(interval_hours)))).isoformat()
    with db() as c:
        c.execute("UPDATE automation_rules SET last_run_at=last_run_at,next_run_at=?,updated_at=? WHERE id=?",(next_run,now(),rule_id))
    return next_run

def approve_knowledge(knowledge_id, approved=True):
    status="ACTIVE" if approved else "ARCHIVED"
    with db() as c:
        cur=c.execute("UPDATE knowledge_entries SET status=?,updated_at=? WHERE id=? AND status='CANDIDATE'",(status,now(),knowledge_id))
        return cur.rowcount>0
