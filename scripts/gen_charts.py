import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import os
import json

os.makedirs('output', exist_ok=True)

# Load real data
with open('output/flight_data.json') as f:
    fd = json.load(f)

top10 = fd['top10Airlines']
airlines = [a['airline'].replace('Turkish Airlines','Turkish').replace('British Airways','British A.') for a in top10]
flights  = [a['flightCount'] for a in top10]
hours    = [a['totalFlightHours'] for a in top10]
blues    = ['#0A2342','#1B4F8A','#1E90D4','#2196F3','#42A5F5','#64B5F6','#90CAF9','#1565C0','#0D47A1','#0288D1']

# Chart 1 — vertical bar: flight counts
fig, ax = plt.subplots(figsize=(13, 5.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
bars = ax.bar(airlines, flights, color=blues[:len(airlines)], width=0.6, zorder=3)
for bar, val in zip(bars, flights):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f'{val:,}',
            ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1E293B')
ax.set_ylabel('Number of Flights', fontsize=11, color='#64748B')
ax.tick_params(colors='#64748B', labelsize=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#E2E8F0')
ax.spines['bottom'].set_color('#E2E8F0')
ax.yaxis.grid(True, color='#E2E8F0', zorder=0)
ax.set_axisbelow(True)
plt.xticks(rotation=15, ha='right')
plt.tight_layout(pad=0.5)
plt.savefig('output/chart_flights.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('chart_flights.png done')

# Chart 2 — horizontal bar: flight hours
fig, ax = plt.subplots(figsize=(13, 5.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
y = np.arange(len(airlines))
bars = ax.barh(y, hours[::-1], color='#1E90D4', height=0.6, zorder=3)
for bar, val in zip(bars, hours[::-1]):
    ax.text(bar.get_width()+0.5, bar.get_y()+bar.get_height()/2, f'{val:,}h',
            ha='left', va='center', fontsize=10, fontweight='bold', color='#1E293B')
ax.set_yticks(y)
ax.set_yticklabels(airlines[::-1], fontsize=10, color='#64748B')
ax.set_xlabel('Total Flight Hours', fontsize=11, color='#64748B')
ax.tick_params(colors='#64748B')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#E2E8F0')
ax.spines['bottom'].set_color('#E2E8F0')
ax.xaxis.grid(True, color='#E2E8F0', zorder=0)
ax.set_axisbelow(True)
plt.tight_layout(pad=0.5)
plt.savefig('output/chart_hours.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('chart_hours.png done')
