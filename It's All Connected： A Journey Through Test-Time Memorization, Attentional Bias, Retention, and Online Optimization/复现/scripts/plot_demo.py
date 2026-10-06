import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parents[1]/'outputs'
r=json.loads((p/'demo_results.json').read_text(encoding='utf8'))
fig,ax=plt.subplots(1,3,figsize=(15,4.4))
colors={'l2':'#c65b50','huber':'#277d9b'}
for mode,offset in [('l2',-.17),('huber',.17)]:
 vals=[r['experiments'][name]['metrics'][mode]['late_mean_mae'] for name in ['clean','contaminated']]
 errs=[r['experiments'][name]['metrics'][mode]['se_of_mean'] for name in ['clean','contaminated']]
 ax[0].bar([0+offset,1+offset],vals,width=.32,color=colors[mode],label=mode.upper(),yerr=errs,capsize=3)
 for i,v in enumerate(vals): ax[0].text(i+offset,v+.015,'%.4f'%v,ha='center',fontsize=9)
ax[0].set_xticks([0,1]); ax[0].set_xticklabels(['Clean','3% outliers'])
ax[0].set_ylim(0,.66);ax[0].set_ylabel('Mean absolute retrieval error');ax[0].set_title('100 episodes; updates 251-500');ax[0].legend()
for mode in colors:
 ax[1].plot(range(1,501),r['experiments']['contaminated']['example']['trace'][mode],color=colors[mode],label=mode.upper(),linewidth=1.2)
 ax[2].plot(range(1,51),r['legitimate_shift'][mode]['trace'],color=colors[mode],label=mode.upper())
ax[1].set_title('Example stream (seed 2026)');ax[1].set_xlabel('Write step');ax[1].set_ylabel('Mean absolute retrieval error');ax[1].legend()
ax[2].axhline(3,color='gray',linestyle='--',label='New true value');ax[2].axhline(2.9,color='gray',linestyle=':',label='Error < 0.1 threshold')
ax[2].set_title('Persistent true-value shift: 1 to 3');ax[2].set_xlabel('Updates after shift');ax[2].set_ylabel('Retrieved value');ax[2].legend(fontsize=8)
for a in ax: a.spines['top'].set_visible(False);a.spines['right'].set_visible(False)
fig.suptitle('MIRAS mechanism demo: robustness and adaptation tradeoff (linear memory)',fontsize=13)
fig.tight_layout(rect=[0,0,1,.93]);fig.savefig(str(p/'demo_summary.png'),dpi=160);fig.savefig(str(p/'demo_summary.svg'));print('Rendered demo_summary.png / .svg')
