import csv, io, json
from pathlib import Path
from .config import MAX_TEXT
ALLOWED={'.txt','.md','.markdown','.csv','.json','.pdf','.docx'}
def extract(filename,payload):
    ext=Path(filename).suffix.lower()
    if ext not in ALLOWED: raise ValueError('不支持此格式。支持：'+', '.join(sorted(ALLOWED)))
    if ext in {'.txt','.md','.markdown','.json','.csv'}:
        text=payload.decode('utf-8-sig',errors='replace')
        if ext=='.json':
            try: text=json.dumps(json.loads(text),ensure_ascii=False,indent=2)
            except json.JSONDecodeError: pass
        elif ext=='.csv':
            try: text='\n'.join(' | '.join(row) for row in csv.reader(io.StringIO(text)))
            except csv.Error: pass
    elif ext=='.pdf':
        try:
            from pypdf import PdfReader
            text='\n\n'.join(p.extract_text() or '' for p in PdfReader(io.BytesIO(payload)).pages)
        except Exception as e: raise ValueError(f'PDF 解析失败：{e}') from e
    else:
        try:
            from docx import Document
            d=Document(io.BytesIO(payload)); text='\n'.join(p.text for p in d.paragraphs)
            for table in d.tables:
                for row in table.rows: text+='\n'+' | '.join(cell.text for cell in row.cells)
        except Exception as e: raise ValueError(f'DOCX 解析失败：{e}') from e
    text=text.replace('\x00','').strip()
    if not text: raise ValueError('未提取到文本；扫描版 PDF 暂不支持 OCR')
    return text[:MAX_TEXT]
