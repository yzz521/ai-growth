from fastapi.testclient import TestClient
from app.main import app

def test_v02_configuration_and_generation_snapshot():
    with TestClient(app) as client:
        brand=client.post("/api/v2/brands",json={"data":{
            "name":"测试品牌","industry":"企业服务","description":"帮助小微企业开展内容营销",
            "products":["AI 内容工作台"],"differentiators":["知识驱动创作"],
            "voice":"专业、直接","cta":"预约演示","is_default":True
        }})
        assert brand.status_code==200
        audience=client.post("/api/v2/audiences",json={"data":{
            "name":"小微企业老板","segment":"1-10 人团队","pain_points":["没有专职内容团队"],
            "goals":["稳定获客"],"objections":["担心 AI 内容同质化"]
        }})
        assert audience.status_code==200
        strategy=client.post("/api/v2/strategies",json={"data":{
            "name":"实用内容策略","pillars":["行业知识","实操教程","真实案例"],
            "ratios":{"行业知识":30,"实操教程":40,"真实案例":30},
            "weekly_frequency":5,"enabled":True
        }})
        assert strategy.status_code==200
        generated=client.post("/api/v2/content/generate",json={
            "topic":"小微企业如何持续生产专业内容",
            "platforms":["xiaohongshu","wechat_official"],
            "brand_id":brand.json()["id"],"audience_id":audience.json()["id"],
            "strategy_id":strategy.json()["id"]
        })
        assert generated.status_code==200
        assert generated.json()["created"]==2
        content_id=generated.json()["items"][0]["id"]
        detail=client.get("/api/content/"+content_id)
        assert detail.status_code==200
        assert detail.json()["generation_context"]["config_snapshot"]["brand_name"]=="测试品牌"

def test_inbox_auto_organize_creates_knowledge_candidate():
    with TestClient(app) as client:
        created=client.post("/api/inbox/text",json={
            "title":"客户内容需求",
            "text":"客户希望下周收到一份内容营销方案，需要联系并跟进。",
            "source_type":"wechat_clip"
        })
        assert created.status_code==201
        candidates=client.get("/api/v2/knowledge/candidates").json()
        assert len(candidates)==1
        assert candidates[0]["status"]=="CANDIDATE"
        approved=client.post("/api/v2/knowledge/"+candidates[0]["id"]+"/approve")
        assert approved.status_code==200
        assert approved.json()["status"]=="ACTIVE"

def test_prompt_platform_and_preferences_are_editable():
    with TestClient(app) as client:
        platform=client.get("/api/v2/platforms").json()
        assert len(platform)>=4
        r=client.put("/api/v2/platforms/xiaohongshu",json={"data":{
            "platform":"xiaohongshu","enabled":False,
            "config":{"format":"图文","structure":["问题","方法","案例"]}
        }})
        assert r.status_code==200
        assert r.json()["enabled"] is False
        prompt=client.post("/api/v2/prompts",json={"data":{
            "code":"xiaohongshu-special","name":"小红书专属规则",
            "platform":"xiaohongshu","body":"使用真实问题，不夸大效果。","active":True
        }})
        assert prompt.status_code==200
        pref=client.put("/api/v2/preferences",json={"data":{"auto_organize":False}})
        assert pref.status_code==200
        assert pref.json()["auto_organize"] is False

def test_automation_rule_and_manual_execution():
    with TestClient(app) as client:
        rule=client.post("/api/v2/automation/rules",json={
            "name":"测试自动整理","rule_type":"auto_organize",
            "config":{"interval_hours":24},"enabled":False
        })
        assert rule.status_code==200
        result=client.post("/api/v2/automation/rules/"+rule.json()["id"]+"/run")
        assert result.status_code==200
        assert result.json()["status"]=="COMPLETED"
        assert len(client.get("/api/v2/automation/runs").json())>=1
