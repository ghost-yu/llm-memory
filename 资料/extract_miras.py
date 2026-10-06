from pathlib import Path
import fitz
p=next(p for p in Path('.').iterdir() if 'All Connected' in p.name)
d=fitz.open(str(p/'原论文.pdf'))
(p/'图片').mkdir(exist_ok=True)
for i in [3,4,7,8,12,13,14,15,16,17,25]:
 d[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(str(p/'图片'/('page-'+str(i+1)+'.png')))
print('rendered',len(d))
