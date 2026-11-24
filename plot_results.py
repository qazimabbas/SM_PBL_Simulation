"""Generate report figures from the simulation output (requires matplotlib)."""
import csv
from pathlib import Path
import matplotlib.pyplot as plt

rows = list(csv.DictReader(Path('results.csv').open()))
labels = ['AM\nNormal', 'AM\nDemand', 'AM\nTraffic', 'PM\nNormal', 'PM\nDemand', 'PM\nTraffic']
for metric, ylabel, filename in [('mean_wait','Mean waiting time (min)','waiting.png'),
                                  ('max_queue','Maximum queue (passengers)','queue.png'),
                                  ('utilization','Peak fleet utilization (%)','utilization.png')]:
    fig, ax = plt.subplots(figsize=(6.7, 2.8), layout='constrained')
    for offset, policy, color in [(-.19,'Fixed','#526579'),(.19,'Adaptive','#147D80')]:
        vals = [float(r[metric]) for r in rows if r['policy']==policy]
        ax.bar([i+offset for i in range(6)], vals, .36, label=policy, color=color)
    ax.set_xticks(range(6), labels, fontsize=9)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
    ax.legend(frameon=False, ncol=2, loc='upper left')
    ax.set_ylim(0, max(float(r[metric]) for r in rows)*1.25)
    fig.savefig(filename, dpi=220); plt.close(fig)
