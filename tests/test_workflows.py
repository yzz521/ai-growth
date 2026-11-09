from app import services
from app.ai import organize
from app.ingest import extract

def test_inbox_knowledge_version():
 x=services.create_inbox('外贸获客资料','外贸企业需要持续发布专业内容。下周需要整理三篇案例。','wechat_clip')
 y=services.organize(x['id']); assert y['status']=='ORGANIZED' and y['summary']
 k=services.inbox_to_knowledge(x['id']); assert k['current_version']==1 and k['source_inbox_id']==x['id']
 u=services.knowledge_update(k['id'],'外贸内容获客',k['content']+' 已确认经验。','更新摘要',['外贸'],'补充')
 assert u['current_version']==2 and len(services.knowledge_get(k['id'])['versions'])==2
 assert services.retrieve('外贸内容')
def test_content_lifecycle_and_lead():
 k=services.create_knowledge('产品介绍','产品适合小微企业内容营销团队。','摘要',['产品'])
 drafts=services.generate('小微企业内容营销',['xiaohongshu','douyin'],[k['id']],'小微企业老板','专业'); assert len(drafts)==2
 d=drafts[0]
 try: services.published(d['id'],None,None); assert False
 except ValueError: pass
 services.approve(d['id']); p=services.published(d['id'],'https://example.com/post/1','测试'); assert p['status']=='PUBLISHED' and len(p['publish_records'])==1
 lead=services.lead_create({'name':'测试客户','source_platform':'xiaohongshu','source_content_id':d['id']}); assert services.lead_update(lead['id'],'CONTACTED','已联系')['status']=='CONTACTED'
def test_extract_reject_and_fallback():
 assert extract('note.md',b'# hi\nbody')=='# hi\nbody'
 try: extract('bad.exe',b'bad'); assert False
 except ValueError: pass
 r=organize('标题','这是一段测试资料。建议下周联系客户。'); assert r['mode']=='local_fallback' and r['tasks']
def test_api_contract(monkeypatch):
 from fastapi.testclient import TestClient
 from app.main import app
 with TestClient(app) as client:
  assert client.get('/api/health').json()['status']=='ok'
  r=client.post('/api/inbox/text',json={'title':'测试资料','text':'小微企业需要稳定内容运营。'}); assert r.status_code==201
  item=r.json(); assert client.post(f"/api/inbox/{item['id']}/organize").status_code==200
  assert client.post(f"/api/inbox/{item['id']}/to-knowledge").status_code==201
  assert len(client.get('/api/knowledge').json())==1
  generated=client.post('/api/content/generate',json={'topic':'测试主题','platforms':['x'],'knowledge_ids':[]}); assert generated.status_code==201

def test_upload_endpoint_and_input_validation(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    import app.main as main_module
    upload_dir = tmp_path / 'uploads'
    upload_dir.mkdir()
    monkeypatch.setattr(main_module, 'UPLOADS', upload_dir)
    with TestClient(app) as client:
        good = client.post('/api/inbox/upload', files={'file': ('wechat-note.md', b'# WeChat\n\nThis is selected text.', 'text/markdown')})
        assert good.status_code == 201
        assert good.json()['title'] == 'wechat-note'
        bad_file = client.post('/api/inbox/upload', files={'file': ('virus.exe', b'x', 'application/octet-stream')})
        assert bad_file.status_code == 400
        bad_url = client.post('/api/content/not-real/record-published', json={'publish_url': 'javascript:alert(1)'})
        assert bad_url.status_code == 422
        bad_status = client.post('/api/leads', json={'name': 'A', 'status': 'HACKED'})
        assert bad_status.status_code == 422
