import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'复现'/'outputs'
r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
fig,axs=plt.subplots(1,2,figsize=(11,4.2))
counts=[sum(x['payload']['user_id']=='alice' for x in s['snapshot']) for s in r['steps'] if s['user']=='alice']
axs[0].plot(range(1,len(counts)+1),counts,marker='o',color='#2464a0')
axs[0].set_xticks(range(1,len(counts)+1));axs[0].set_xticklabels(['ADD city','ADD hobby','NONE','UPDATE city','DELETE hobby','Bad JSON'],rotation=30,ha='right')
axs[0].set_ylabel('Active records for Alice');axs[0].set_ylim(0,3);axs[0].set_title('Original methods: observed state changes')
axs[1].bar(['Infer + consolidation','infer=False'],[len(r['searches']['alice']['results']),len(r['searches']['raw']['results'])],color=['#2464a0','#d89534'])
axs[1].set_ylim(0,4);axs[1].set_ylabel('Retrieved city records');axs[1].set_title('Controlled provider; not LLM accuracy')
fig.tight_layout();fig.savefig(str(OUT/'mechanism.png'),dpi=160);fig.savefig(str(OUT/'mechanism.svg'));plt.close(fig)
