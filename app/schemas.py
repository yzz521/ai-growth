from pydantic import BaseModel, Field, field_validator
class InboxText(BaseModel):
 title:str=Field(default='未命名资料',min_length=1,max_length=200); text:str=Field(min_length=1,max_length=100000); source_type:str=Field(default='manual',max_length=40); source_name:str|None=Field(default=None,max_length=200)
class KnowledgeCreate(BaseModel):
 title:str=Field(min_length=1,max_length=200); content:str=Field(min_length=1,max_length=100000); summary:str|None=Field(default=None,max_length=2000); tags:list[str]=Field(default_factory=list,max_length=20)
class KnowledgeUpdate(KnowledgeCreate): change_reason:str=Field(default='人工更新',max_length=300)
class Ask(BaseModel): question:str=Field(min_length=1,max_length=2000); limit:int=Field(default=5,ge=1,le=10)
class Generate(BaseModel):
 topic:str=Field(min_length=1,max_length=300); platforms:list[str]=Field(min_length=1,max_length=4); knowledge_ids:list[str]=Field(default_factory=list,max_length=20); audience:str=Field(default='目标客户',max_length=200); tone:str=Field(default='专业、可信、易懂',max_length=100)
 @field_validator('platforms')
 @classmethod
 def valid_platforms(cls,v):
  v=list(dict.fromkeys(x.strip().lower() for x in v)); invalid=set(v)-{'xiaohongshu','douyin','x','wechat_official'}
  if invalid: raise ValueError('不支持的平台：'+','.join(invalid))
  if not v: raise ValueError('至少选择一个平台')
  return v
class ContentUpdate(BaseModel): title:str=Field(min_length=1,max_length=300); body:str=Field(min_length=1,max_length=12000)
class PublishRecord(BaseModel):
 publish_url:str|None=Field(default=None,max_length=1000); note:str|None=Field(default=None,max_length=1000)
 @field_validator('publish_url')
 @classmethod
 def safe_url(cls,v):
  if v and not v.strip().lower().startswith(('https://','http://')): raise ValueError('发布链接仅允许 http:// 或 https://')
  return v
class LeadCreate(BaseModel):
 name:str=Field(min_length=1,max_length=120); company:str|None=Field(default=None,max_length=200); contact:str|None=Field(default=None,max_length=200); source_platform:str|None=Field(default=None,max_length=40); source_content_id:str|None=None; requirement:str|None=Field(default=None,max_length=2000); budget:str|None=Field(default=None,max_length=100); status:str=Field(default='NEW',max_length=40); notes:str|None=Field(default=None,max_length=2000)
 @field_validator('status')
 @classmethod
 def valid_status(cls,v):
  if v not in {'NEW','CONTACTED','QUALIFIED','WON','LOST'}: raise ValueError('无效的线索状态')
  return v
class LeadUpdate(BaseModel):
 status:str=Field(min_length=1,max_length=40); notes:str|None=Field(default=None,max_length=2000)
 @field_validator('status')
 @classmethod
 def valid_status(cls,v):
  if v not in {'NEW','CONTACTED','QUALIFIED','WON','LOST'}: raise ValueError('无效的线索状态')
  return v
