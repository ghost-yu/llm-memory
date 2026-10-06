"""Plot the saved measured demo results; does not run or train a model."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parents[2]
out=BASE/'复现'/'outputs'
r=json.loads((out/'demo_results.json').read_text(encoding='utf-8'))
fig, axes=plt.subplots(1,2,figsize=(12,4.3))
ax=axes[0]
items=[r[k] for k in ('linear_reference','deep_before','deep_after')]
x=list(range(3))
for offset,key,label,color in ((-.18,'written_accuracy','After writing','#29867f'),(.18,'reset_accuracy','After memory reset','#a9b4c4')):
    heights=[v[key]*100 for v in items]
    ax.bar([t+offset for t in x],heights,width=.34,label=label,color=color)
    for t,h in zip(x,heights): ax.text(t+offset,h+1.8,'%.1f%%'%h,ha='center',fontsize=9)
ax.axhline(12.5,color='#bd5f38',linestyle='--',linewidth=1,label='Chance: 12.5%')
ax.set_xticks(x)
ax.set_xticklabels(['Linear reference','Depth 2: before','Depth 2: after'])
ax.set_ylim(0,118)
ax.set_ylabel('Query accuracy (%)')
ax.set_title('256 independent test episodes / 2048 queries')
ax.legend(loc='upper center',bbox_to_anchor=(.5,1.01),fontsize=8,ncol=3)
ax=axes[1]
ax.plot([v['step'] for v in r['history']],[v['loss'] for v in r['history']],color='#29867f',marker='o',markersize=3)
ax.set_xlabel('Outer meta-training step')
ax.set_ylabel('Cross-entropy (scaled readout)')
ax.set_title('Training minibatch loss; batches change each step')
ax.grid(alpha=.2)
fig.suptitle('Titans NeuralMemory component: synthetic 8-key task with fixed encodings',fontsize=12)
fig.tight_layout(rect=[0,0,1,.93])
fig.savefig(str(out/'demo_summary.png'),dpi=160)
fig.savefig(str(out/'demo_summary.svg'))
print(str(out/'demo_summary.png'))
