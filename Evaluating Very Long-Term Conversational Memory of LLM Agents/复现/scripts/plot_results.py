import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs';r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
fig,axs=plt.subplots(1,2,figsize=(12,4.6));ks=r['configuration']['k_values']
axs[0].plot(ks,[r['overall']['bm25'][str(k)]*100 for k in ks],marker='o',color='#3268a3',label='BM25')
axs[0].axhline(r['overall']['recent10']*100,color='#c78b35',ls='--',label='Recent 10 turns')
axs[0].set_xlabel('Retrieved turns, k');axs[0].set_ylabel('Mean evidence coverage (%)');axs[0].set_ylim(0,100);axs[0].legend();axs[0].set_title('1,536 annotated non-adversarial questions')
cats=['1','2','3','4'];x=np.arange(4);vals=[r['by_category'][c]['bm25']['10']*100 for c in cats]
axs[1].bar(x,vals,color='#3268a3');axs[1].set_xticks(x);axs[1].set_xticklabels(['Multi-hop\nn=282','Temporal\nn=321','Open\nn=92','Single-hop\nn=841']);axs[1].set_ylim(0,100);axs[1].set_title('BM25 top10: category evidence coverage')
for a,v in zip(x,vals):axs[1].text(a,v+2,'%.2f%%'%v,ha='center',fontsize=10)
fig.text(.5,.015,'True released LoCoMo data; lexical retrieval only, no answer model or QA accuracy',ha='center');fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(str(OUT/'retrieval.png'),dpi=160);fig.savefig(str(OUT/'retrieval.svg'));plt.close(fig)
