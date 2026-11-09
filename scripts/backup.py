import os,sqlite3,zipfile
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=Path(os.getenv('AGW_DATA_DIR',ROOT/'data')); DB=Path(os.getenv('AGW_DB_PATH',DATA/'app.db'))
def main():
 if not DB.exists(): print('数据库不存在：',DB); return 1
 out=DATA/'backups'; out.mkdir(parents=True,exist_ok=True); tmp=out/'snapshot.db'; src=sqlite3.connect(DB); dst=sqlite3.connect(tmp)
 try: src.backup(dst)
 finally: dst.close(); src.close()
 archive=out/f'agw_backup_{datetime.now():%Y%m%d_%H%M%S}.zip'
 try:
  with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
   z.write(tmp,'app.db'); uploads=DATA/'uploads'
   if uploads.exists():
    for f in uploads.rglob('*'):
     if f.is_file(): z.write(f,Path('uploads')/f.relative_to(uploads))
  print('备份完成：',archive)
 finally: tmp.unlink(missing_ok=True)
 return 0
if __name__=='__main__': raise SystemExit(main())
