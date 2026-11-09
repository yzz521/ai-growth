import asyncio
from datetime import datetime, timedelta, timezone
from . import v02_store as store
from .v02_api import execute_rule

def _due(value):
    if not value:
        return False
    try:
        return datetime.fromisoformat(value.replace("Z","+00:00")) <= datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False

async def scheduler_loop():
    while True:
        try:
            for rule in store.list_records("rules",200):
                if not rule["enabled"]:
                    continue
                next_at=rule.get("next_run_at")
                if not next_at:
                    interval=int((rule.get("config") or {}).get("interval_hours",24))
                    store.schedule_rule(rule["id"],interval)
                    continue
                if _due(next_at):
                    try:
                        await asyncio.to_thread(execute_rule,rule=rule)
                    except Exception:
                        pass
                    interval=max(1,int((rule.get("config") or {}).get("interval_hours",24)))
                    store.schedule_rule(rule["id"],interval)
        except Exception:
            pass
        await asyncio.sleep(15)
