import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
root=Path(__file__).resolve().parent;out=root/'figures'
results=root.parent/'results'
out.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':9,'axes.labelsize':9,'legend.fontsize':7.5,'xtick.labelsize':8,'ytick.labelsize':9,'pdf.fonttype':42})
rows=json.loads((results/'summary.json').read_text())
variants=['baseline','o2','stack','o2-stack','sorted','hoist-fixed','final']
labels=['Baseline','O2','Stack','O2 + stack','+ sorting','+ hoist fix','Final']
colors=['#999999','#0072B2','#E69F00','#009E73','#CC79A7','#56B4E9','#555555']
fig,ax=plt.subplots(figsize=(3.35,2.25),layout='constrained');x=np.arange(3);width=.11
for i,(v,l,c) in enumerate(zip(variants,labels,colors)):
 vals=[next(r['speedup'] for r in rows if r['variant']==v and r['dataset']==d) for d in ['diabetes','cancer','housing']]
 ax.bar(x+(i-3)*width,vals,width,label=l,color=c)
ax.set_xticks(x,['Diabetes','Cancer','Housing']);ax.set_ylabel('Speedup over baseline');ax.set_ylim(0,19)
ax.legend(ncol=3,loc='upper left',frameon=False,columnspacing=.55,handlelength=.9)
ax.set_axisbelow(True);ax.grid(axis='y',alpha=.2)
for ext in ['pdf','png']:fig.savefig(out/f'stages.{ext}',dpi=220)
plt.close(fig)
over=json.loads((results/'all-summary.json').read_text())
fig,ax=plt.subplots(figsize=(3.35,1.85),layout='constrained')
names=[r['title'] for r in over['workloads']]
vals=[r['baseline']['internal_seconds']['median']/r['final']['internal_seconds']['median'] for r in over['workloads']]
ax.barh(names,vals,color='#0072B2',height=.6);ax.invert_yaxis();ax.set_xlim(0,15)
for i,v in enumerate(vals):ax.text(v+.15,i,f'{v:.2f}x',va='center',fontsize=8.5)
ax.set_xlabel('Final speedup over baseline');ax.set_axisbelow(True);ax.grid(axis='x',alpha=.2)
for ext in ['pdf','png']:fig.savefig(out/f'overview.{ext}',dpi=220)
plt.close(fig)
