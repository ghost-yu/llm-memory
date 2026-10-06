import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parents[1]/'outputs'
r=json.loads((p/'demo_results.json').read_text(encoding='utf8'))
fig,ax=plt.subplots(1,2,figsize=(11.5,4.5))
check=r['checks']['recall_after_eviction'];vals=[int(check['fifo_has_answer_before_search']),int(check['result_reentered_context'])]
ax[0].bar([0,1],vals,color=['#bd5c50','#277d9b'],width=.55)
ax[0].set_xticks([0,1]);ax[0].set_xticklabels(['After FIFO eviction','After recall search']);ax[0].set_ylim(0,1.25);ax[0].set_yticks([0,1]);ax[0].set_ylabel('Answer text present in bounded context');ax[0].set_title('Evicted information can re-enter context')
for i,v in enumerate(vals):ax[0].text(i,v+.05,str(v),ha='center')
for name,label,color,marker in [('full_correct','Paginate + chain','#277d9b','o'),('first_page_correct','First page only','#bd5c50','s'),('one_call_correct','One tool call only','#6b6c84','x')]:
 y=[r['summary'][str(d)][name] for d in [1,2,3,4]];ax[1].plot([1,2,3,4],y,label=label,color=color,marker=marker)
ax[1].set_xticks([1,2,3,4]);ax[1].set_ylim(-.1,1.3);ax[1].set_yticks([0,.5,1]);ax[1].set_xlabel('KV links (not paper nesting-level convention)');ax[1].set_ylabel('Exact-answer rate, 5 trials per depth');ax[1].set_title('Deterministic controller; later-page key records');ax[1].legend(fontsize=9,loc='upper center',ncol=1)
for a in ax:a.spines['top'].set_visible(False);a.spines['right'].set_visible(False)
fig.suptitle('MemGPT mechanism demo: official tools + SQLite, no LLM',fontsize=13)
fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(str(p/'demo_summary.png'),dpi=160);fig.savefig(str(p/'demo_summary.svg'));print('Rendered demo figures')
