import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=Path(__file__).resolve().parents[1]/'outputs'
r=json.loads((p/'demo_results.json').read_text(encoding='utf8'))
fig,ax=plt.subplots(1,3,figsize=(15,4.7))
colors={'every_step':'#bc594d','cms':'#217f9b','all_slow':'#6b6c84'}
labels={'every_step':'Every step [1,1,1]','cms':'CMS [1,16,64]','all_slow':'All slow [64,64,64]'}
for mode in colors:
 traces=[q['models'][mode]['trace_before_write'] for q in r['runs']]
 accuracy=np.mean([[z['changed_accuracy_current'] for z in tr] for tr in traces],axis=0)
 old=np.mean([[z['mse_old_A'] for z in tr] for tr in traces],axis=0)
 ax[0].plot(range(1,641),accuracy,color=colors[mode],label=labels[mode])
 ax[1].plot(range(1,641),old,color=colors[mode],label=labels[mode])
for a in ax[:2]:
 a.axvspan(129,384,color='#eadac3',alpha=.3);a.axvline(128,color='gray',linestyle=':');a.axvline(384,color='gray',linestyle=':');a.set_xlabel('Stream step (read before update)')
ax[0].set_title('Changed-key recall: current mapping');ax[0].set_ylabel('Accuracy (mean of 5 seeds)');ax[0].set_ylim(-.05,1.12);ax[0].text(245,1.035,'Task B',ha='center');ax[0].legend(fontsize=8,loc='lower right')
ax[1].set_title('Old mapping A: forgetting and relearning');ax[1].set_ylabel('MSE on mapping A (mean of 5 seeds)');ax[1].legend(fontsize=8)
for mode,offset in [('every_step',-.25),('cms',0),('all_slow',.25)]:
 vals=r['summary'][mode]['updates_per_block'];pos=np.arange(3)+offset
 ax[2].bar(pos,vals,width=.23,color=colors[mode],label=labels[mode])
 for x,v in zip(pos,vals): ax[2].text(x,v*1.15,str(v),ha='center',fontsize=8)
ax[2].set_xticks([0,1,2]);ax[2].set_xticklabels(['Block 1','Block 2','Block 3']);ax[2].set_yscale('log');ax[2].set_ylim(1,2000);ax[2].set_ylabel('Actual parameter updates (log scale)');ax[2].set_title('Same 1,656 parameters in all models')
for a in ax: a.spines['top'].set_visible(False);a.spines['right'].set_visible(False)
fig.suptitle('Nested Learning / CMS mechanism demo: A -> B -> A, supervised toy stream',fontsize=13)
fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(str(p/'demo_summary.png'),dpi=160);fig.savefig(str(p/'demo_summary.svg'));print('Rendered demo_summary.png and .svg')
