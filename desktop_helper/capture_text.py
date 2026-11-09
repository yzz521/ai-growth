import argparse,re,sys
from datetime import datetime
from pathlib import Path
DROP=Path(__file__).resolve().parents[1]/'data'/'dropbox'
def main():
 p=argparse.ArgumentParser(description='保存用户主动选定的文本'); p.add_argument('title',nargs='?',default='微信剪藏'); p.add_argument('--text'); a=p.parse_args(); text=a.text if a.text is not None else sys.stdin.read()
 if not text.strip(): print('没有收到文本',file=sys.stderr); return 2
 DROP.mkdir(parents=True,exist_ok=True); name=re.sub(r'[^\w\-\u4e00-\u9fff]+','_',a.title).strip('_')[:50] or 'capture'; path=DROP/f'{datetime.now():%Y%m%d_%H%M%S}_{name}.md'; path.write_text(f'# {a.title}\n\n{text.strip()}\n',encoding='utf-8'); print('已保存：',path); return 0
if __name__=='__main__': raise SystemExit(main())
