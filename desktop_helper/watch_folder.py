import argparse, json, mimetypes, time, urllib.request, urllib.error, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DROP=ROOT/'data'/'dropbox'; DONE=DROP/'processed'; SUPPORTED={'.txt','.md','.markdown','.csv','.json','.pdf','.docx'}
def upload(url,p):
 b='----AGW'+uuid.uuid4().hex; name=p.name.replace('"','_'); data=p.read_bytes(); mime=mimetypes.guess_type(name)[0] or 'application/octet-stream'; out=bytearray()
 for field,value in [('source_type','local_desktop_helper'),('title',p.stem)]: out.extend(f'--{b}\r\nContent-Disposition: form-data; name="{field}"\r\n\r\n{value}\r\n'.encode())
 out.extend(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()); out.extend(data); out.extend(f'\r\n--{b}--\r\n'.encode())
 req=urllib.request.Request(url,data=bytes(out),headers={'Content-Type':f'multipart/form-data; boundary={b}'},method='POST')
 with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--api',default='http://127.0.0.1:8000'); ap.add_argument('--interval',type=float,default=2); ap.add_argument('--once',action='store_true'); a=ap.parse_args(); DROP.mkdir(parents=True,exist_ok=True); DONE.mkdir(parents=True,exist_ok=True); print('监控目录：',DROP,'；只处理用户主动保存的文件。')
 while True:
  for p in [x for x in DROP.iterdir() if x.is_file() and x.suffix.lower() in SUPPORTED and not x.name.startswith('.')]:
   try:
    size=p.stat().st_size; time.sleep(.2)
    if p.stat().st_size!=size: continue
    result=upload(a.api.rstrip('/')+'/api/inbox/upload',p); p.rename(DONE/f'{p.stem}-{result["id"][:8]}{p.suffix}'); print('已导入：',p.name)
   except urllib.error.HTTPError as e: print('导入失败：',e.code,e.read().decode(errors='replace')[:300])
   except Exception as e: print('导入失败：',p.name,e)
  if a.once: return 0
  time.sleep(max(.5,a.interval))
if __name__=='__main__': raise SystemExit(main())
