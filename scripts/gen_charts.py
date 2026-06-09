import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os, json

os.makedirs('output', exist_ok=True)

with open('output/flight_data.json') as f:
    fd = json.load(f)

top10 = fd['top10Airlines']
airlines = [a['airline'].replace('Turkish Airlines','Turkish A.').replace('British Airways','British A.').replace('TAP Air Portugal','TAP Portugal') for a in top10]
flights  = [a['flightCount'] for a in top10]
hours    = [a['totalFlightHours'] for a in top10]

# Color palette — deep aviation blues + one gold accent for #1
colors = ['#C9A84C','#1B3F6E','#1E5F9B','#2474B5','#2E8BC0','#3AA0D4','#48B4E0','#14325C','#0D2B4E','#0A2040']

# ── Chart 1: Horizontal bar — flight counts ──────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 6))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8FAFC')

y = np.arange(len(airlines))
bars = ax.barh(y, flights[::-1], color=colors[::-1], height=0.62, zorder=3)

for bar, val in zip(bars, flights[::-1]):
    ax.text(bar.get_width() + max(flights)*0.01, bar.get_y()+bar.get_height()/2,
            f'{val:,}', ha='left', va='center', fontsize=10, fontweight='bold', color='#1B3F6E')

ax.set_yticks(y)
ax.set_yticklabels(airlines[::-1], fontsize=10, color='#334155')
ax.set_xlabel('Flights Tracked', fontsize=11, color='#64748B', labelpad=8)
ax.tick_params(colors='#94A3B8', left=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#E2E8F0')
ax.xaxis.grid(True, color='#E2E8F0', zorder=0, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_xlim(0, max(flights) * 1.18)
plt.tight_layout(pad=0.8)
plt.savefig('output/chart_flights.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('chart_flights.png done')

# ── Chart 2: Vertical bar — block hours ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, 5.5))
fig.patch.set_facecolor('white')
ax.set_facecolor('#F8FAFC')

bars = ax.bar(airlines, hours, color=colors, width=0.6, zorder=3)
for bar, val in zip(bars, hours):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+max(hours)*0.01,
            f'{val:,}h', ha='center', va='bottom', fontsize=9, fontweight='bold', color='#1B3F6E')

ax.set_ylabel('Block Hours', fontsize=11, color='#64748B', labelpad=8)
ax.tick_params(colors='#94A3B8', bottom=False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#E2E8F0')
ax.spines['bottom'].set_visible(False)
ax.yaxis.grid(True, color='#E2E8F0', zorder=0, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_ylim(0, max(hours) * 1.15)
plt.xticks(rotation=18, ha='right', fontsize=9.5, color='#334155')
plt.tight_layout(pad=0.8)
plt.savefig('output/chart_hours.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('chart_hours.png done')

# ── Chart 3: Pie chart — market share by flights ─────────────────────────────
fig, ax = plt.subplots(figsize=(9, 7))
fig.patch.set_facecolor('white')

total = sum(flights)
# Only show label for airlines with >5% share, rest grouped
threshold = 0.05
labels_pie = []
sizes_pie  = []
colors_pie = []
other = 0
for i, (a, f) in enumerate(zip(airlines, flights)):
    if f/total >= threshold:
        labels_pie.append(f'{a}\n{f/total*100:.1f}%')
        sizes_pie.append(f)
        colors_pie.append(colors[i])
    else:
        other += f

if other > 0:
    labels_pie.append(f'Others\n{other/total*100:.1f}%')
    sizes_pie.append(other)
    colors_pie.append('#94A3B8')

wedges, texts = ax.pie(
    sizes_pie, labels=labels_pie, colors=colors_pie,
    startangle=140, counterclock=False,
    wedgeprops={'linewidth':2, 'edgecolor':'white'},
    textprops={'fontsize':10, 'color':'#1E293B', 'fontweight':'bold'}
)

# Draw a white circle in the center for donut effect
centre_circle = plt.Circle((0,0), 0.55, fc='white')
ax.add_artist(centre_circle)
ax.text(0, 0.08, 'Market', ha='center', va='center', fontsize=13, color='#64748B')
ax.text(0, -0.18, 'Share', ha='center', va='center', fontsize=13, color='#64748B')

ax.axis('equal')
plt.tight_layout(pad=0.5)
plt.savefig('output/chart_pie.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
print('chart_pie.png done')
