import re
import sqlite3
import uuid

from . import ai
from .db import db, dump, load, now, row

def uid():
    return str(uuid.uuid4())

def create_inbox(title, text, source_type="manual", source_name=None,
                 original_filename=None, stored_filename=None):
    item_id=uid()
    ts=now()
    with db() as conn:
        conn.execute(
            """INSERT INTO inbox_items(
                id,source_type,source_name,title,raw_text,status,
                original_filename,stored_filename,created_at,updated_at
            ) VALUES(?,?,?,?,?,'PENDING',?,?,?,?)""",
            (item_id,source_type,source_name,title,text,original_filename,stored_filename,ts,ts)
        )
        return row(conn.execute("SELECT * FROM inbox_items WHERE id=?",(item_id,)).fetchone())

def inbox_list(status=None,limit=100):
    with db() as conn:
        sql="SELECT * FROM inbox_items"
        params=[]
        if status:
            sql+=" WHERE status=?"
            params.append(status)
        sql+=" ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return [row(x) for x in conn.execute(sql,params).fetchall()]

def inbox_get(item_id):
    with db() as conn:
        return row(conn.execute("SELECT * FROM inbox_items WHERE id=?",(item_id,)).fetchone())

def organize(item_id):
    item=inbox_get(item_id)
    if not item:
        raise KeyError("收件箱资料不存在")
    result=ai.organize(item["title"],item["raw_text"])
    with db() as conn:
        conn.execute(
            """UPDATE inbox_items SET summary=?,tags_json=?,extracted_json=?,
               status='ORGANIZED',updated_at=? WHERE id=?""",
            (result.get("summary",""),dump(result.get("tags",[])),dump(result),now(),item_id)
        )
    return inbox_get(item_id)

def _new_knowledge(conn,title,content,summary,tags,source_id,source_type,source_ref,status="ACTIVE"):
    knowledge_id=uid()
    ts=now()
    conn.execute(
        """INSERT INTO knowledge_entries(
           id,title,content,summary,tags_json,source_inbox_id,source_type,
           source_ref,status,current_version,created_at,updated_at
        ) VALUES(?,?,?,?,?,?,?,?,?,1,?,?)""",
        (knowledge_id,title,content,summary,dump(tags),source_id,source_type,source_ref,status,ts,ts)
    )
    conn.execute(
        """INSERT INTO knowledge_versions(
           id,knowledge_id,version_no,content,summary,change_reason,created_at
        ) VALUES(?,?,?,?,?,?,?)""",
        (uid(),knowledge_id,1,content,summary,"首次创建",ts)
    )
    return knowledge_id

def inbox_to_knowledge(item_id,title=None,status="ACTIVE"):
    item=inbox_get(item_id)
    if not item:
        raise KeyError("收件箱资料不存在")
    if not item.get("summary"):
        organize(item_id)
        item=inbox_get(item_id)
    suggested=(item.get("extracted") or {}).get("suggested_knowledge_title")
    final_title=title or suggested or item["title"]
    with db() as conn:
        existing=conn.execute(
            "SELECT * FROM knowledge_entries WHERE source_inbox_id=? AND status<>'ARCHIVED' ORDER BY created_at DESC LIMIT 1",
            (item_id,)
        ).fetchone()
        if existing:
            if existing["status"]=="CANDIDATE" and status=="ACTIVE":
                conn.execute("UPDATE knowledge_entries SET status='ACTIVE',updated_at=? WHERE id=?",(now(),existing["id"]))
                existing=conn.execute("SELECT * FROM knowledge_entries WHERE id=?",(existing["id"],)).fetchone()
            conn.execute("UPDATE inbox_items SET status='SAVED',updated_at=? WHERE id=?",(now(),item_id))
            return row(existing)
        knowledge_id=_new_knowledge(
            conn,final_title,item["raw_text"],item.get("summary"),item.get("tags",[]),
            item_id,item["source_type"],item.get("source_name") or item.get("original_filename"),status
        )
        conn.execute("UPDATE inbox_items SET status='SAVED',updated_at=? WHERE id=?",(now(),item_id))
        return row(conn.execute("SELECT * FROM knowledge_entries WHERE id=?",(knowledge_id,)).fetchone())

def inbox_to_candidate(item_id):
    item=inbox_get(item_id)
    if not item:
        raise KeyError("收件箱资料不存在")
    if not item.get("summary"):
        organize(item_id)
    with db() as conn:
        existing=conn.execute(
            "SELECT * FROM knowledge_entries WHERE source_inbox_id=? AND status<>'ARCHIVED' ORDER BY created_at DESC LIMIT 1",
            (item_id,)
        ).fetchone()
        if existing:
            return row(existing)
    return inbox_to_knowledge(item_id,status="CANDIDATE")

def create_knowledge(title,content,summary,tags):
    with db() as conn:
        knowledge_id=_new_knowledge(conn,title,content,summary,tags,None,"manual",None,"ACTIVE")
        return row(conn.execute("SELECT * FROM knowledge_entries WHERE id=?",(knowledge_id,)).fetchone())

def knowledge_candidates(limit=100):
    with db() as conn:
        return [
            row(x) for x in conn.execute(
                "SELECT * FROM knowledge_entries WHERE status='CANDIDATE' ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        ]

def knowledge_list(q=None,limit=100):
    with db() as conn:
        if q and q.strip():
            term="%"+q.strip()+"%"
            records=conn.execute(
                """SELECT * FROM knowledge_entries
                   WHERE status='ACTIVE' AND
                   (title LIKE ? OR content LIKE ? OR summary LIKE ? OR tags_json LIKE ?)
                   ORDER BY updated_at DESC LIMIT ?""",
                (term,term,term,term,limit)
            ).fetchall()
        else:
            records=conn.execute(
                "SELECT * FROM knowledge_entries WHERE status='ACTIVE' ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [row(x) for x in records]

def knowledge_get(knowledge_id):
    with db() as conn:
        result=row(conn.execute("SELECT * FROM knowledge_entries WHERE id=?",(knowledge_id,)).fetchone())
        if result:
            result["versions"]=[
                dict(x) for x in conn.execute(
                    """SELECT version_no,change_reason,created_at FROM knowledge_versions
                       WHERE knowledge_id=? ORDER BY version_no DESC""",
                    (knowledge_id,)
                ).fetchall()
            ]
        return result

def knowledge_update(knowledge_id,title,content,summary,tags,reason):
    with db() as conn:
        old=conn.execute("SELECT * FROM knowledge_entries WHERE id=?",(knowledge_id,)).fetchone()
        if not old:
            raise KeyError("知识不存在")
        version=old["current_version"]+1
        ts=now()
        conn.execute(
            """UPDATE knowledge_entries SET title=?,content=?,summary=?,tags_json=?,
               current_version=?,updated_at=? WHERE id=?""",
            (title,content,summary,dump(tags),version,ts,knowledge_id)
        )
        conn.execute(
            """INSERT INTO knowledge_versions(
               id,knowledge_id,version_no,content,summary,change_reason,created_at
            ) VALUES(?,?,?,?,?,?,?)""",
            (uid(),knowledge_id,version,content,summary,reason,ts)
        )
    return knowledge_get(knowledge_id)

def _terms(text):
    words={x.lower() for x in re.findall(r"[A-Za-z0-9_-]{2,}",text)}
    chars=re.findall(r"[\u4e00-\u9fff]",text)
    words.update(chars[i]+chars[i+1] for i in range(len(chars)-1))
    return words

def retrieve(query,limit=5):
    query_terms=_terms(query)
    ranked=[]
    for item in knowledge_list(limit=500):
        body=" ".join([
            item["title"],item.get("summary") or "",item["content"],
            " ".join(item.get("tags",[]))
        ])
        terms=_terms(body)
        overlap=len(query_terms & terms)
        score=overlap/max(len(query_terms),1)
        if query.strip() and query.strip() in body:
            score+=3
        if score:
            ranked.append((score,item))
    ranked.sort(key=lambda pair:pair[0],reverse=True)
    return [item for _,item in ranked[:limit]]

def ask(query,limit):
    return ai.answer(query,retrieve(query,limit))

def generate(topic,platforms,knowledge_ids,audience,tone,context="",meta=None):
    selected=[]
    if knowledge_ids:
        placeholders=",".join("?" for _ in knowledge_ids)
        with db() as conn:
            selected=[
                row(x) for x in conn.execute(
                    f"SELECT * FROM knowledge_entries WHERE status='ACTIVE' AND id IN ({placeholders})",
                    tuple(knowledge_ids)
                ).fetchall()
            ]
    output=[]
    for platform in platforms:
        result=ai.generate(topic,platform,audience,tone,selected,context)
        content_id=uid()
        ts=now()
        with db() as conn:
            conn.execute(
                """INSERT INTO content_drafts(
                    id,topic,platform,audience,tone,title,body,source_knowledge_ids_json,
                    status,generated_mode,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,'DRAFT',?,?,?)""",
                (content_id,topic,platform,audience,tone,result["title"],result["body"],
                 dump(knowledge_ids),result["mode"],ts,ts)
            )
            if meta is not None:
                try:
                    conn.execute(
                        """INSERT INTO content_generation_context(
                            content_id,brand_id,audience_id,strategy_id,prompt_versions_json,
                            config_snapshot_json,created_at
                        ) VALUES(?,?,?,?,?,?,?)""",
                        (content_id,meta.get("brand_id"),meta.get("audience_id"),meta.get("strategy_id"),
                         dump(meta.get("prompt_versions",{})),dump(meta),ts)
                    )
                except sqlite3.OperationalError:
                    # Direct service tests may not have run the app lifespan migrations.
                    pass
            output.append(row(conn.execute("SELECT * FROM content_drafts WHERE id=?",(content_id,)).fetchone()))
    return output

def content_list(status=None,limit=100):
    with db() as conn:
        sql="SELECT * FROM content_drafts"
        params=[]
        if status:
            sql+=" WHERE status=?"
            params.append(status)
        sql+=" ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        return [row(x) for x in conn.execute(sql,params).fetchall()]

def content_get(content_id):
    with db() as conn:
        result=row(conn.execute("SELECT * FROM content_drafts WHERE id=?",(content_id,)).fetchone())
        if not result:
            return None
        result["publish_records"]=[
            dict(x) for x in conn.execute(
                "SELECT * FROM publish_records WHERE content_id=? ORDER BY created_at DESC",
                (content_id,)
            ).fetchall()
        ]
        try:
            context=conn.execute(
                "SELECT * FROM content_generation_context WHERE content_id=?",(content_id,)
            ).fetchone()
        except sqlite3.OperationalError:
            context=None
        if context:
            result["generation_context"]={
                "brand_id":context["brand_id"],
                "audience_id":context["audience_id"],
                "strategy_id":context["strategy_id"],
                "prompt_versions":load(context["prompt_versions_json"],{}),
                "config_snapshot":load(context["config_snapshot_json"],{}),
                "created_at":context["created_at"],
            }
        return result

def content_update(content_id,title,body):
    with db() as conn:
        item=conn.execute("SELECT status FROM content_drafts WHERE id=?",(content_id,)).fetchone()
        if not item:
            raise KeyError("内容草稿不存在")
        if item["status"]=="PUBLISHED":
            raise ValueError("已发布内容不能直接修改")
        conn.execute(
            "UPDATE content_drafts SET title=?,body=?,updated_at=? WHERE id=?",
            (title,body,now(),content_id)
        )
    return content_get(content_id)

def approve(content_id):
    with db() as conn:
        item=conn.execute("SELECT status FROM content_drafts WHERE id=?",(content_id,)).fetchone()
        if not item:
            raise KeyError("内容草稿不存在")
        if item["status"]=="PUBLISHED":
            raise ValueError("内容已经发布")
        conn.execute(
            "UPDATE content_drafts SET status='APPROVED',updated_at=? WHERE id=?",
            (now(),content_id)
        )
    return content_get(content_id)

def published(content_id,url,note):
    with db() as conn:
        item=conn.execute("SELECT * FROM content_drafts WHERE id=?",(content_id,)).fetchone()
        if not item:
            raise KeyError("内容草稿不存在")
        if item["status"] not in ("APPROVED","PUBLISHED"):
            raise ValueError("请先审核通过内容，再记录发布")
        ts=now()
        conn.execute(
            """INSERT INTO publish_records(
               id,content_id,platform,publish_url,status,published_at,note,created_at
            ) VALUES(?,?,?,?,'PUBLISHED_MANUALLY',?,?,?)""",
            (uid(),content_id,item["platform"],url,ts,note,ts)
        )
        conn.execute(
            "UPDATE content_drafts SET status='PUBLISHED',updated_at=? WHERE id=?",
            (ts,content_id)
        )
    return content_get(content_id)

def lead_create(payload):
    lead_id=uid()
    ts=now()
    with db() as conn:
        conn.execute(
            """INSERT INTO leads(
               id,name,company,contact,source_platform,source_content_id,
               requirement,budget,status,notes,created_at,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (lead_id,payload["name"],payload.get("company"),payload.get("contact"),
             payload.get("source_platform"),payload.get("source_content_id"),
             payload.get("requirement"),payload.get("budget"),payload.get("status","NEW"),
             payload.get("notes"),ts,ts)
        )
        return dict(conn.execute("SELECT * FROM leads WHERE id=?",(lead_id,)).fetchone())

def lead_list(limit=100):
    with db() as conn:
        return [dict(x) for x in conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ?",(limit,)
        ).fetchall()]

def lead_update(lead_id,status,notes):
    with db() as conn:
        if not conn.execute("SELECT 1 FROM leads WHERE id=?",(lead_id,)).fetchone():
            raise KeyError("线索不存在")
        conn.execute(
            "UPDATE leads SET status=?,notes=?,updated_at=? WHERE id=?",
            (status,notes,now(),lead_id)
        )
        return dict(conn.execute("SELECT * FROM leads WHERE id=?",(lead_id,)).fetchone())

def dashboard():
    with db() as conn:
        counts={
            "inbox_pending":conn.execute(
                "SELECT COUNT(*) FROM inbox_items WHERE status IN ('PENDING','ORGANIZED')"
            ).fetchone()[0],
            "knowledge":conn.execute(
                "SELECT COUNT(*) FROM knowledge_entries WHERE status='ACTIVE'"
            ).fetchone()[0],
            "content_pending":conn.execute(
                "SELECT COUNT(*) FROM content_drafts WHERE status IN ('DRAFT','APPROVED')"
            ).fetchone()[0],
            "open_leads":conn.execute(
                "SELECT COUNT(*) FROM leads WHERE status NOT IN ('WON','LOST')"
            ).fetchone()[0],
        }
        recent_inbox=[
            dict(x) for x in conn.execute(
                "SELECT id,title,source_type,status,created_at FROM inbox_items ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
        ]
        recent_content=[
            dict(x) for x in conn.execute(
                "SELECT id,title,platform,status,created_at FROM content_drafts ORDER BY created_at DESC LIMIT 5"
            ).fetchall()
        ]
        return {"counts":counts,"recent_inbox":recent_inbox,"recent_content":recent_content}
