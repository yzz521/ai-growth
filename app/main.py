import logging, uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from . import ai, services
from .config import UPLOADS, MAX_UPLOAD, ensure_dirs
from .db import init_db
from .ingest import extract
from .schemas import InboxText, KnowledgeCreate, KnowledgeUpdate, Ask, Generate, ContentUpdate, PublishRecord, LeadCreate, LeadUpdate
logging.basicConfig(level=logging.INFO)
log=logging.getLogger('agw')
@asynccontextmanager
async def lifespan(app):
    ensure_dirs()
    init_db()
    yield
app=FastAPI(title='AI Growth Workspace',version='0.1.0',description='本地单用户 MVP；默认不自动发布第三方平台内容。',lifespan=lifespan)
@app.get('/api/health')
def health(): return {'status':'ok','version':'0.1.0'}
@app.get('/api/settings')
def settings():
 from .config import AI_MODEL
 return {'ai_configured':ai.configured(),'model':AI_MODEL,'mode':'remote_ai' if ai.configured() else 'local_fallback','platforms':{k:{'generation':True,'publishing':'manual'} for k in ('xiaohongshu','douyin','x','wechat_official')},'notice':'当前只生成草稿并记录人工发布，不会自动登录或发布第三方平台。'}
@app.get('/api/dashboard')
def dashboard(): return services.dashboard()
@app.get('/api/inbox')
def inbox_list(status:str|None=None,limit:int=100): return services.inbox_list(status,max(1,min(limit,200)))
@app.post('/api/inbox/text',status_code=201)
def inbox_text(p:InboxText): return services.create_inbox(p.title,p.text,p.source_type,p.source_name)
@app.post('/api/inbox/upload',status_code=201)
async def inbox_upload(file:UploadFile=File(...),source_type:str=Form('file'),title:str|None=Form(None)):
 filename=Path(file.filename or 'upload.txt').name[:240]
 if not Path(filename).suffix: raise HTTPException(400,'上传文件必须有扩展名')
 payload=await file.read(MAX_UPLOAD+1)
 if len(payload)>MAX_UPLOAD: raise HTTPException(413,f'文件超过 {MAX_UPLOAD//(1024*1024)} MB 限制')
 try: text=extract(filename,payload)
 except ValueError as e: raise HTTPException(400,str(e))
 stored=uuid.uuid4().hex+Path(filename).suffix.lower(); path=UPLOADS/stored; path.write_bytes(payload)
 try: return services.create_inbox(title or Path(filename).stem, text, source_type, filename, filename, stored)
 except Exception: path.unlink(missing_ok=True); raise
@app.get('/api/inbox/{i}')
def inbox_get(i):
 x=services.inbox_get(i)
 if not x: raise HTTPException(404,'收件箱资料不存在')
 return x
@app.post('/api/inbox/{i}/organize')
def inbox_organize(i):
 try: return services.organize(i)
 except KeyError as e: raise HTTPException(404,str(e))
@app.post('/api/inbox/{i}/to-knowledge',status_code=201)
def inbox_save(i,title:str|None=None):
 try: return services.inbox_to_knowledge(i,title)
 except KeyError as e: raise HTTPException(404,str(e))
@app.get('/api/knowledge')
def knowledge_list(q:str|None=None,limit:int=100): return services.knowledge_list(q,max(1,min(limit,200)))
@app.post('/api/knowledge',status_code=201)
def knowledge_create(p:KnowledgeCreate): return services.create_knowledge(p.title,p.content,p.summary,p.tags)
@app.get('/api/knowledge/{i}')
def knowledge_get(i):
 x=services.knowledge_get(i)
 if not x: raise HTTPException(404,'知识不存在')
 return x
@app.put('/api/knowledge/{i}')
def knowledge_update(i,p:KnowledgeUpdate):
 try: return services.knowledge_update(i,p.title,p.content,p.summary,p.tags,p.change_reason)
 except KeyError as e: raise HTTPException(404,str(e))
@app.post('/api/knowledge/ask')
def knowledge_ask(p:Ask): return services.ask(p.question,p.limit)
@app.post('/api/content/generate',status_code=201)
def content_generate(p:Generate):
 try: return services.generate(p.topic,p.platforms,p.knowledge_ids,p.audience,p.tone)
 except Exception as e: log.exception('generate failed'); raise HTTPException(502,f'内容生成失败：{str(e)[:300]}')
@app.get('/api/content')
def content_list(status:str|None=None,limit:int=100): return services.content_list(status,max(1,min(limit,200)))
@app.get('/api/content/{i}')
def content_get(i):
 x=services.content_get(i)
 if not x: raise HTTPException(404,'内容草稿不存在')
 return x
@app.put('/api/content/{i}')
def content_update(i,p:ContentUpdate):
 try: return services.content_update(i,p.title,p.body)
 except KeyError as e: raise HTTPException(404,str(e))
 except ValueError as e: raise HTTPException(409,str(e))
@app.post('/api/content/{i}/approve')
def content_approve(i):
 try: return services.approve(i)
 except KeyError as e: raise HTTPException(404,str(e))
 except ValueError as e: raise HTTPException(409,str(e))
@app.post('/api/content/{i}/record-published')
def content_published(i,p:PublishRecord):
 try: return services.published(i,p.publish_url,p.note)
 except KeyError as e: raise HTTPException(404,str(e))
 except ValueError as e: raise HTTPException(409,str(e))
@app.get('/api/leads')
def leads_list(limit:int=100): return services.lead_list(max(1,min(limit,200)))
@app.post('/api/leads',status_code=201)
def leads_create(p:LeadCreate):
 if p.source_content_id and not services.content_get(p.source_content_id): raise HTTPException(400,'关联内容不存在')
 return services.lead_create(p.model_dump())
@app.patch('/api/leads/{i}')
def leads_update(i,p:LeadUpdate):
 try: return services.lead_update(i,p.status,p.notes)
 except KeyError as e: raise HTTPException(404,str(e))
STATIC=Path(__file__).resolve().parent/'static'
app.mount('/static',StaticFiles(directory=STATIC),name='static')
@app.get('/',include_in_schema=False)
def home(): return FileResponse(STATIC/'index.html')
