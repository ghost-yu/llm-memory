from pathlib import Path
import fitz
ROOT=Path(__file__).resolve().parents[1];P=next(ROOT.glob('A-MEM*'));(P/'图片').mkdir(exist_ok=True);(P/'代码').mkdir(exist_ok=True)
doc=fitz.open(str(P/'原论文.pdf'))
(P/'资料'/'全文.txt').write_text('\n'.join('=== PAGE %d ===\n%s'%(i+1,p.get_text()) for i,p in enumerate(doc)),encoding='utf-8')
for i,p in enumerate(doc):p.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(str(P/'图片'/('page-%d.png'%(i+1))))
print('pages',len(doc))
