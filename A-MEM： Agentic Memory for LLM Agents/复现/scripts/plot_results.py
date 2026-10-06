import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
fig,axs=plt.subplots(1,2,figsize=(12,4.5));ax=axs[0];ax.set_xlim(-.1,1.1);ax.set_ylim(0,1);ax.axis('off')
points={'art':(.15,.70),'cache':(.45,.30),'lru':(.85,.70)}
labels={'art':'0: Art note','cache':'1: Cache note\ncontext evolved','lru':'2: LRU note'}
for key,(x,y) in points.items():ax.text(x,y,labels[key],ha='center',va='center',bbox=dict(boxstyle='round,pad=.5',facecolor='#e9f0f7',edgecolor='#3268a3'))
for n in r['final']:
    for idx in n['links']:
        target=r['final'][idx]['id'];x,y=points[n['id']];a,b=points[target]
        ax.annotate('',xy=(a+.07,b+.08),xytext=(x-.06,y-.06),arrowprops=dict(arrowstyle='->',lw=2,color='#3268a3'))
ax.set_title('Observed link: LRU -> Cache (position 1)')
ax=axs[1];ax.axis('off');ax.set_title('Evolved object vs delayed search index')
cache=next(n for n in r['final'] if n['id']=='cache')
lines=[('Memory object',cache['context']),('Index before consolidation',next(n for n in r['steps'][1]['notes'] if n['id']=='cache')['context']),('Index after consolidation',cache['context'])]
for i,(label,value) in enumerate(lines):
    y=.8-i*.27;ax.text(.02,y,label,weight='bold',fontsize=11);ax.text(.02,y-.09,value,fontsize=11,color='#245b8e')
fig.text(.5,.015,'Original methods, controlled JSON responses and hash vectors; not LLM accuracy',ha='center',fontsize=10)
fig.tight_layout(rect=[0,.04,1,1]);fig.savefig(str(OUT/'mechanism.png'),dpi=160);fig.savefig(str(OUT/'mechanism.svg'));plt.close(fig)
