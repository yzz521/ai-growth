import re, uuid
from . import ai
from .db import db, dump, now, row

def uid(): return str(uuid.uuid4())
def create_inbox(title,text,source_type='manual',source_name=None,original_filename=None,stored_filename=None):
 i=uid(); t=now()
 with db() as c:
  c.execute("INSERT INTO inbox_items(id,source_type,source_name,title,raw_text,status,original_filename,stored_filename,created_at,updated_at) VALUES(?,?,?,?,?,'PENDING',?,?,?,?)",(i,source_type,source_name,title,text,original_filename,stored_filename,t,t)); r=c.execute('SELECT * FROM inbox_items WHERE id=?',(i,)).fetchone()
 return row(r)
def inbox_list(status=None,limit=100):
 with db() as c:
  q='SELECT * FROM inbox_items'; p=[]
  if status: q+=' WHERE status=?'; p.append(status)
  q+=' ORDER BY created_at DESC LIMIT ?'; p.append(limit); return [row(x) for x in c.execute(q,p).fetchall()]
def inbox_get(i):
 with db() as c: return row(c.execute('SELECT * FROM inbox_items WHERE id=?',(i,)).fetchone())
def organize(i):
 item=inbox_get(i)
 if not item: raise KeyError('收件箱资料不存在')
 result=ai.organize(item['title'],item['raw_text'])
 with db() as c: c.execute("UPDATE inbox_items SET summary=?,tags_json=?,extracted_json=?,status='ORGANIZED',updated_at=? WHERE id=?",(result.get('summary',''),dump(result.get('tags',[])),dump(result),now(),i))
 return inbox_get(i)
def _new_knowledge(c,title,content,summary,tags,source_id,source_type,source_ref):
 i=uid(); t=now(); c.execute("INSERT INTO knowledge_entries(id,title,content,summary,tags_json,source_inbox_id,source_type,source_ref,status,current_version,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,'ACTIVE',1,?,?)",(i,title,content,summary,dump(tags),source_id,source_type,source_ref,t,t)); c.execute('INSERT INTO knowledge_versions(id,knowledge_id,version_no,content,summary,change_reason,created_at) VALUES(?,?,?,?,?,?,?)',(uid(),i,1,content,summary,'首次创建',t)); return i
def inbox_to_knowledge(i,title=None):
 item=inbox_get(i)
 if not item: raise KeyError('收件箱资料不存在')
 if not item.get('summary'): organize(i); item=inbox_get(i)
 title=title or (item.get('extracted') or {}).get('suggested_knowledge_title') or item['title']
 with db() as c:
  k=_new_knowledge(c,title,item['raw_text'],item.get('summary'),item.get('tags',[]),i,item['source_type'],item.get('source_name') or item.get('original_filename')); c.execute("UPDATE inbox_items SET status='SAVED',updated_at=? WHERE id=?",(now(),i)); return row(c.execute('SELECT * FROM knowledge_entries WHERE id=?',(k,)).fetchone())
def create_knowledge(title,content,summary,tags):
 with db() as c: i=_new_knowledge(c,title,content,summary,tags,None,'manual',None); return row(c.execute('SELECT * FROM knowledge_entries WHERE id=?',(i,)).fetchone())
def knowledge_list(q=None,limit=100):
 with db() as c:
  if q:
   p='%'+q.strip()+'%'; rs=c.execute("SELECT * FROM knowledge_entries WHERE status='ACTIVE' AND (title LIKE ? OR content LIKE ? OR summary LIKE ? OR tags_json LIKE ?) ORDER BY updated_at DESC LIMIT ?",(p,p,p,p,limit)).fetchall()
  else: rs=c.execute("SELECT * FROM knowledge_entries WHERE status='ACTIVE' ORDER BY updated_at DESC LIMIT ?",(limit,)).fetchall()
  return [row(x) for x in rs]
def knowledge_get(i):
 with db() as c:
  r=row(c.execute('SELECT * FROM knowledge_entries WHERE id=?',(i,)).fetchone())
  if r: r['versions']=[dict(x) for x in c.execute('SELECT version_no,change_reason,created_at FROM knowledge_versions WHERE knowledge_id=? ORDER BY version_no DESC',(i,)).fetchall()]
  return r
def knowledge_update(i,title,content,summary,tags,reason):
 with db() as c:
  old=c.execute('SELECT * FROM knowledge_entries WHERE id=?',(i,)).fetchone()
  if not old: raise KeyError('知识不存在')
  v=old['current_version']+1; t=now(); c.execute('UPDATE knowledge_entries SET title=?,content=?,summary=?,tags_json=?,current_version=?,updated_at=? WHERE id=?',(title,content,summary,dump(tags),v,t,i)); c.execute('INSERT INTO knowledge_versions(id,knowledge_id,version_no,content,summary,change_reason,created_at) VALUES(?,?,?,?,?,?,?)',(uid(),i,v,content,summary,reason,t))
 return knowledge_get(i)
def terms(text):
 words={x.lower() for x in re.findall(r'[A-Za-z0-9_-]{2,}',text)}; chars=re.findall(r'[\u4e00-\u9fff]',text); words.update(chars[i]+chars[i+1] for i in range(len(chars)-1)); return words
def retrieve(q,limit=5):
 ranked=[]; qt=terms(q)
 for x in knowledge_list(limit=500):
  body=' '.join([x['title'],x.get('summary') or '',x['content'],' '.join(x.get('tags',[]))]); ht=terms(body); overlap=len(qt & ht); score=overlap/max(len(qt),1)+(3 if q.strip() and q.strip() in body else 0)
  if score: ranked.append((score,x))
 ranked.sort(key=lambda z:z[0],reverse=True); return [x for _,x in ranked[:limit]]
def ask(q,limit): return ai.answer(q,retrieve(q,limit))
def generate(topic,platforms,kids,audience,tone):
 selected=[]
 if kids:
  with db() as c:
   marks=','.join('?' for _ in kids); selected=[row(x) for x in c.execute(f"SELECT * FROM knowledge_entries WHERE status='ACTIVE' AND id IN ({marks})",tuple(kids)).fetchall()]
 out=[]
 for p in platforms:
  result=ai.generate(topic,p,audience,tone,selected); i=uid(); t=now()
  with db() as c:
   c.execute("INSERT INTO content_drafts(id,topic,platform,audience,tone,title,body,source_knowledge_ids_json,status,generated_mode,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,'DRAFT',?,?,?)",(i,topic,p,audience,tone,result['title'],result['body'],dump(kids),result['mode'],t,t)); out.append(row(c.execute('SELECT * FROM content_drafts WHERE id=?',(i,)).fetchone()))
 return out
def content_list(status=None,limit=100):
 with db() as c:
  q='SELECT * FROM content_drafts'; p=[]
  if status: q+=' WHERE status=?'; p.append(status)
  q+=' ORDER BY created_at DESC LIMIT ?'; p.append(limit); return [row(x) for x in c.execute(q,p).fetchall()]
def content_get(i):
 with db() as c:
  r=row(c.execute('SELECT * FROM content_drafts WHERE id=?',(i,)).fetchone())
  if r: r['publish_records']=[dict(x) for x in c.execute('SELECT * FROM publish_records WHERE content_id=? ORDER BY created_at DESC',(i,)).fetchall()]
  return r
def content_update(i,title,body):
 with db() as c:
  r=c.execute('SELECT status FROM content_drafts WHERE id=?',(i,)).fetchone()
  if not r: raise KeyError('内容草稿不存在')
  if r['status']=='PUBLISHED': raise ValueError('已发布内容不能直接修改')
  c.execute('UPDATE content_drafts SET title=?,body=?,updated_at=? WHERE id=?',(title,body,now(),i))
 return content_get(i)
def approve(i):
 with db() as c:
  r=c.execute('SELECT status FROM content_drafts WHERE id=?',(i,)).fetchone()
  if not r: raise KeyError('内容草稿不存在')
  if r['status']=='PUBLISHED': raise ValueError('内容已经发布')
  c.execute("UPDATE content_drafts SET status='APPROVED',updated_at=? WHERE id=?",(now(),i))
 return content_get(i)
def published(i,url,note):
 with db() as c:
  r=c.execute('SELECT * FROM content_drafts WHERE id=?',(i,)).fetchone()
  if not r: raise KeyError('内容草稿不存在')
  if r['status'] not in ('APPROVED','PUBLISHED'): raise ValueError('请先审核通过内容，再记录发布')
  t=now(); c.execute("INSERT INTO publish_records(id,content_id,platform,publish_url,status,published_at,note,created_at) VALUES(?,?,?,?,'PUBLISHED_MANUALLY',?,?,?)",(uid(),i,r['platform'],url,t,note,t)); c.execute("UPDATE content_drafts SET status='PUBLISHED',updated_at=? WHERE id=?",(t,i))
 return content_get(i)
def lead_create(p):
 i=uid(); t=now()
 with db() as c:
  c.execute('INSERT INTO leads(id,name,company,contact,source_platform,source_content_id,requirement,budget,status,notes,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(i,p['name'],p.get('company'),p.get('contact'),p.get('source_platform'),p.get('source_content_id'),p.get('requirement'),p.get('budget'),p.get('status','NEW'),p.get('notes'),t,t)); return dict(c.execute('SELECT * FROM leads WHERE id=?',(i,)).fetchone())
def lead_list(limit=100):
 with db() as c: return [dict(x) for x in c.execute('SELECT * FROM leads ORDER BY created_at DESC LIMIT ?',(limit,)).fetchall()]
def lead_update(i,status,notes):
 with db() as c:
  if not c.execute('SELECT 1 FROM leads WHERE id=?',(i,)).fetchone(): raise KeyError('线索不存在')
  c.execute('UPDATE leads SET status=?,notes=?,updated_at=? WHERE id=?',(status,notes,now(),i)); return dict(c.execute('SELECT * FROM leads WHERE id=?',(i,)).fetchone())
def dashboard():
 with db() as c:
  counts={'inbox_pending':c.execute("SELECT COUNT(*) FROM inbox_items WHERE status IN ('PENDING','ORGANIZED')").fetchone()[0],'knowledge':c.execute("SELECT COUNT(*) FROM knowledge_entries WHERE status='ACTIVE'").fetchone()[0],'content_pending':c.execute("SELECT COUNT(*) FROM content_drafts WHERE status IN ('DRAFT','APPROVED')").fetchone()[0],'open_leads':c.execute("SELECT COUNT(*) FROM leads WHERE status NOT IN ('WON','LOST')").fetchone()[0]}
  return {'counts':counts,'recent_inbox':[dict(x) for x in c.execute('SELECT id,title,source_type,status,created_at FROM inbox_items ORDER BY created_at DESC LIMIT 5').fetchall()],'recent_content':[dict(x) for x in c.execute('SELECT id,title,platform,status,created_at FROM content_drafts ORDER BY created_at DESC LIMIT 5').fetchall()]}
