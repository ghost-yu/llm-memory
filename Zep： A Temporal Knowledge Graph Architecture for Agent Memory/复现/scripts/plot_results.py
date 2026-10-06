import json
from pathlib import Path
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'复现'/'outputs'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
start=datetime(2025,1,1)
def days(s):return (datetime.fromisoformat(s).replace(tzinfo=None)-start).days
rows=[e for e in r['final'] if e['user']=='alice'];rows.sort(key=lambda e:e['valid_at'])
fig,ax=plt.subplots(figsize=(10,4.6))
colors=['#3268a3','#dc9b37','#499974']
for i,e in enumerate(rows):
    a=days(e['valid_at']);b=days(e['invalid_at']) if e['invalid_at'] else 125
    ax.barh(i,b-a,left=a,height=.32,color=colors[i],label='Valid interval' if i==0 else None)
    ax.scatter(days(e['created_at']),i,marker='D',color='#ad3344',s=65,label='Received / created' if i==0 else None,zorder=3)
ax.set_yticks(range(len(rows)));ax.set_yticklabels([e['value'] for e in rows]);ax.invert_yaxis()
ax.set_xticks([0,31,59,90,120]);ax.set_xticklabels(['Jan 1','Feb 1','Mar 1','Apr 1','May 1'])
ax.set_xlim(-3,128);ax.set_title('Alice: fact validity differs from arrival time');ax.set_xlabel('2025, UTC; intervals are half-open');ax.legend(loc='lower right');ax.grid(axis='x',alpha=.2)
fig.tight_layout();fig.savefig(str(OUT/'temporal.png'),dpi=160);fig.savefig(str(OUT/'temporal.svg'));plt.close(fig)
