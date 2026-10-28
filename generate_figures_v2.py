"""
generate_figures_v2.py
Publication-grade visual asset generator for ASA DataQuest 2026.
Bespoke editorial aesthetic matching elite statistical publications (The Economist, Nature, Financial Times).
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
from sklearn.linear_model import RidgeCV

# Configure global publication styling
plt.rcParams['font.sans-serif'] = ['Segoe UI', 'DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#CBD5E1'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['xtick.color'] = '#475569'
plt.rcParams['ytick.color'] = '#475569'
plt.rcParams['text.color'] = '#0F172A'
plt.rcParams['figure.autolayout'] = False

os.makedirs('figures_v2', exist_ok=True)

# 1. Load Data
print("Loading core datasets...")
df_master = pd.read_csv('materials/WPP2024_Master_Dataset.csv', low_memory=False)
df_zero = pd.read_csv('materials/WPP2024_ZeroMigration_2050.csv')

# Filter sovereign nations N=155 (Pop >= 1M in 2000)
df_2000 = df_master[(df_master['Time'] == 2000) & (df_master['TPopulation1July'] >= 1000.0)].copy()
sovereign_locs = df_2000['Location'].unique()

# Extract 2000 and 2020 observations for these sovereign locations
df_hist = df_master[(df_master['Location'].isin(sovereign_locs)) & (df_master['Time'].isin([2000, 2020]))].copy()

# Pivot median age
df_med = df_hist.pivot(index='Location', columns='Time', values='MedianAgePop').dropna()
df_med['MedianAge_Delta'] = df_med[2020] - df_med[2000]

# Add Region
loc_to_region = df_hist.drop_duplicates(subset=['Location']).set_index('Location')['Region'].to_dict()
df_med['Region'] = df_med.index.map(loc_to_region)
df_analysis = df_med.reset_index()

print(f"Sovereign nations analyzed: {len(df_analysis)}")

# ==============================================================================
# FIGURE 2: REGIONAL VELOCITY DIVERGENCE (Publication Edition)
# ==============================================================================
print("Generating Figure 2: Regional Velocity Divergence...")

# Order regions by median acceleration
regional_medians = df_analysis.groupby('Region')['MedianAge_Delta'].median().sort_values(ascending=False)
order = regional_medians.index.tolist()

fig, ax = plt.subplots(figsize=(8.5, 5.0), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')

# Palette: Terracotta/Coral for fast developing, Slate/Navy for mature, Gold/Gray for others
palette_map = {
    'Latin America and the Caribbean': '#C2410C',
    'Asia': '#0284C7',
    'Europe': '#1E293B',
    'Northern America': '#475569',
    'Oceania': '#64748B',
    'Africa': '#D97706'
}
box_colors = [palette_map.get(r, '#475569') for r in order]

# Boxplot
bp = ax.boxplot(
    [df_analysis[df_analysis['Region'] == r]['MedianAge_Delta'].values for r in order],
    positions=range(len(order)),
    patch_artist=True,
    widths=0.48,
    showmeans=True,
    meanline=True,
    medianprops=dict(color='#0F172A', linewidth=1.8),
    meanprops=dict(color='#DC2626', linewidth=1.5, linestyle='--'),
    whiskerprops=dict(color='#94A3B8', linewidth=1.2),
    capprops=dict(color='#94A3B8', linewidth=1.2),
    flierprops=dict(marker='', markersize=0) # Hide default fliers to use jitter
)

for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.35)
    patch.set_edgecolor(color)
    patch.set_linewidth(1.5)

# Jitter points
np.random.seed(42)
for i, r in enumerate(order):
    vals = df_analysis[df_analysis['Region'] == r]['MedianAge_Delta'].values
    jitter = np.random.uniform(-0.15, 0.15, size=len(vals))
    ax.scatter(i + jitter, vals, color=palette_map.get(r, '#475569'), alpha=0.75, s=28, edgecolors='#FFFFFF', linewidths=0.5, zorder=4)

# Format axes
ax.set_xticks(range(len(order)))
clean_labels = [
    'Latin America\n& Caribbean\n(+6.61y)',
    'Asia\n(+6.02y)',
    'Europe\n(+5.69y)',
    'Northern\nAmerica\n(+3.53y)',
    'Oceania\n(+2.97y)',
    'Africa\n(+1.79y)'
]
ax.set_xticklabels(clean_labels, fontsize=9.5, fontweight='medium', color='#1E293B')
ax.set_ylabel('20-Year Rise in Median Age (Years, 2000 → 2020)', fontsize=10.5, fontweight='bold', color='#0F172A', labelpad=8)
ax.set_ylim(-2.5, 14.5)
ax.yaxis.grid(True, linestyle='-', linewidth=0.6, color='#E2E8F0', alpha=0.8, zorder=0)
ax.xaxis.grid(False)

# Clean spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CBD5E1')
ax.spines['bottom'].set_color('#CBD5E1')

# Outlier callouts (South Korea, Iran, Thailand, Puerto Rico)
annotations = [
    ('Puerto Rico (+13.0y)', 0, 13.0, 0.25, 13.4),
    ('Rep. of Korea (+12.1y)', 1, 12.1, 1.25, 12.8),
    ('Iran (+11.1y)', 1, 11.1, 1.25, 11.6),
    ('Thailand (+9.2y)', 1, 9.2, 1.25, 9.8)
]
for text, x_pt, y_pt, x_txt, y_txt in annotations:
    ax.annotate(
        text,
        xy=(x_pt, y_pt),
        xytext=(x_txt, y_txt),
        fontsize=8.0,
        fontweight='bold',
        color='#0F172A',
        arrowprops=dict(arrowstyle='->', color='#475569', lw=0.9, shrinkA=2, shrinkB=2)
    )

# Subtle legend for means vs medians
ax.plot([], [], color='#0F172A', linewidth=1.8, label='Regional Median')
ax.plot([], [], color='#DC2626', linewidth=1.5, linestyle='--', label='Regional Mean')
ax.legend(loc='upper right', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=8.0)

plt.tight_layout()
plt.savefig('figures_v2/fig2_velocity_v2.png', dpi=300, facecolor='#FFFFFF', bbox_inches='tight')
plt.close()
print("Figure 2 saved.")

# ==============================================================================
# FIGURE 3: FOREST PLOT (Standardized Ridge Betas)
# ==============================================================================
print("Generating Figure 3: Driver Forest Plot...")

# Ridge betas and bootstrap CIs from rigorous pipeline
drivers = [
    ('Lagged Fertility (TFR 2000)', -3.211, -3.758, -2.693, '< 0.0001 (Dominant)'),
    ('Starting Median Age (2000)', -2.120, -2.810, -1.512, '< 0.0001'),
    ('Apex Longevity (ΔLE65)', 0.715, 0.201, 1.262, '< 0.0001'),
    ('Adult Health (ΔQ1560)', 0.680, 0.321, 1.007, '< 0.0001'),
    ('Net Migration Rate (CNMR)', -0.174, -0.764, 0.415, '0.289 (Not Significant)')
]

fig, ax = plt.subplots(figsize=(10.5, 4.5), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')

y_pos = range(len(drivers)-1, -1, -1)
names = [d[0] for d in drivers]
betas = [d[1] for d in drivers]
ci_lows = [d[2] for d in drivers]
ci_highs = [d[3] for d in drivers]
p_texts = [d[4] for d in drivers]

# Vertical reference line at 0 (Null hypothesis)
ax.axvline(0, color='#DC2626', linestyle='--', linewidth=1.2, alpha=0.85, zorder=2)
ax.text(0.04, 4.35, 'Null (β = 0)', color='#DC2626', fontsize=8.2, fontweight='bold')

# Tabular column headers on right
ax.text(1.6, 4.35, 'Std. Beta (β)', fontweight='bold', fontsize=8.8, color='#0F172A', va='center')
ax.text(2.8, 4.35, '95% Bootstrap CI', fontweight='bold', fontsize=8.8, color='#0F172A', va='center')
ax.text(4.4, 4.35, 'p-value', fontweight='bold', fontsize=8.8, color='#0F172A', va='center')
ax.plot([1.5, 5.6], [4.10, 4.10], color='#CBD5E1', linewidth=0.8)

for i, (y, beta, low, high, p_txt) in enumerate(zip(y_pos, betas, ci_lows, ci_highs, p_texts)):
    is_null = (low <= 0 <= high)
    point_color = '#64748B' if is_null else '#0F2C59'
    bar_color = '#94A3B8' if is_null else '#0284C7'
    
    # Error bar
    ax.plot([low, high], [y, y], color=bar_color, linewidth=2.5, solid_capstyle='round', zorder=3)
    ax.plot([low, low], [y - 0.12, y + 0.12], color=bar_color, linewidth=2.0, zorder=3)
    ax.plot([high, high], [y - 0.12, y + 0.12], color=bar_color, linewidth=2.0, zorder=3)
    
    # Beta point
    ax.scatter(beta, y, color=point_color, s=75, edgecolors='#FFFFFF', linewidths=1.2, zorder=4)
    
    # Tabular stats on right
    ax.text(1.6, y, f"{beta:+.3f}", va='center', fontsize=8.8, fontweight='bold', color='#0F172A')
    ax.text(2.8, y, f"[{low:+.2f}, {high:+.2f}]", va='center', fontsize=8.5, color='#334155')
    p_color = '#64748B' if is_null else '#0F2C59'
    ax.text(4.4, y, p_txt, va='center', fontsize=8.5, fontweight='medium', color=p_color)

ax.set_yticks(y_pos)
ax.set_yticklabels(names, fontsize=9.5, fontweight='bold', color='#0F172A')
ax.set_xlabel('Standardized Ridge Beta Coefficient', fontsize=9.5, fontweight='bold', color='#0F172A', labelpad=8)
ax.set_xlim(-4.2, 5.8)
ax.set_ylim(-0.6, 4.8)

ax.xaxis.grid(True, linestyle='-', linewidth=0.6, color='#E2E8F0', alpha=0.8, zorder=0)
ax.yaxis.grid(False)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CBD5E1')
ax.spines['bottom'].set_color('#CBD5E1')

ax.set_title("Standardized Ridge Predictors of Ageing Velocity (N = 155)", fontsize=10.0, fontweight='bold', color='#0F2C59', pad=10, loc='left')

plt.tight_layout()
plt.savefig('figures_v2/fig3_forest_v2.png', dpi=300, facecolor='#FFFFFF', bbox_inches='tight')
plt.close()
print("Figure 3 saved.")

# ==============================================================================
# FIGURE 5: MIGRATION COUNTERFACTUAL (Actuarial Proof)
# ==============================================================================
print("Generating Figure 5: Migration Counterfactual...")

# Query UN Zero-Migration vs Medium Variant 2050 from df_zero and df_master
top_destinations = [
    ('United States of America', 'USA'),
    ('Canada', 'Canada'),
    ('Germany', 'Germany'),
    ('United Kingdom', 'UK'),
    ('Australia', 'Australia')
]

countries = []
med_variants = []
zero_variants = []
deltas = []

for full_name, short_name in top_destinations:
    row_zero = df_zero[(df_zero['Location'] == full_name) & (df_zero['Time'] == 2050)]
    row_med = df_master[(df_master['Location'] == full_name) & (df_master['Time'] == 2050)]
    
    if len(row_zero) > 0 and len(row_med) > 0:
        val_z = float(row_zero['MedianAgePop'].values[0])
        val_m = float(row_med['MedianAgePop'].values[0])
        delta = val_z - val_m
        countries.append(short_name)
        med_variants.append(val_m)
        zero_variants.append(val_z)
        deltas.append(delta)

fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')

x = np.arange(len(countries))
width = 0.36

rects1 = ax.bar(x - width/2, med_variants, width, label='UN Medium Projection (With Migration)', color='#0284C7', edgecolor='#0369A1', linewidth=1.0, zorder=3)
rects2 = ax.bar(x + width/2, zero_variants, width, label='UN Zero-Migration Variant (Zero Borders)', color='#DC2626', edgecolor='#B91C1C', linewidth=1.0, zorder=3)

# Data labels showing exact deltas
for i in range(len(countries)):
    z_val = zero_variants[i]
    d_val = deltas[i]
    ax.annotate(
        f"+{d_val:.2f} yrs",
        xy=(x[i] + width/2, z_val),
        xytext=(0, 5),
        textcoords="offset points",
        ha='center',
        va='bottom',
        fontsize=8.5,
        fontweight='bold',
        color='#991B1B'
    )
    # Also subtle value inside the bars
    ax.text(x[i] - width/2, med_variants[i] - 3.5, f"{med_variants[i]:.1f}", ha='center', va='center', fontsize=8.0, color='#FFFFFF', fontweight='bold')
    ax.text(x[i] + width/2, zero_variants[i] - 3.5, f"{zero_variants[i]:.1f}", ha='center', va='center', fontsize=8.0, color='#FFFFFF', fontweight='bold')

ax.set_ylabel('Projected 2050 Median Age (Years)', fontsize=10.0, fontweight='bold', color='#0F172A', labelpad=8)
ax.set_xticks(x)
ax.set_xticklabels(countries, fontsize=10.0, fontweight='bold', color='#1E293B')
ax.set_ylim(35.0, 53.5)

ax.yaxis.grid(True, linestyle='-', linewidth=0.6, color='#E2E8F0', alpha=0.8, zorder=0)
ax.xaxis.grid(False)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CBD5E1')
ax.spines['bottom'].set_color('#CBD5E1')

ax.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=8.5)

# Clean layout without in-chart overlapping footnote
ax.set_title("2050 Projected Median Age: Medium vs. Zero-Migration", fontsize=10.0, fontweight='bold', color='#0F2C59', pad=10, loc='left')

plt.tight_layout()
plt.savefig('figures_v2/fig5_migration_v2.png', dpi=300, facecolor='#FFFFFF', bbox_inches='tight')
plt.close()
print("Figure 5 saved.")

# ==============================================================================
# FIGURE 4: PROSPECTIVE AGEING SCATTERPLOT
# ==============================================================================
print("Generating Figure 4: Prospective Ageing...")

df_supp = pd.read_csv('materials/WPP2024_Supplement_Births_and_LE60.csv', low_memory=False)

# Merge LE60/LE65 into 2020 sovereign nations
df_2020_master = df_master[(df_master['Location'].isin(sovereign_locs)) & (df_master['Time'] == 2020)].copy()
df_2000_supp = df_supp[(df_supp['Location'].isin(sovereign_locs)) & (df_supp['Time'] == 2000)].copy()
df_2020_supp = df_supp[(df_supp['Location'].isin(sovereign_locs)) & (df_supp['Time'] == 2020)].copy()

m_le = pd.merge(
    df_2000_supp[['Location', 'LE60']].rename(columns={'LE60': 'LE60_2000'}),
    df_2020_supp[['Location', 'LE60']].rename(columns={'LE60': 'LE60_2020'}),
    on='Location'
)
m_le['dLE60'] = m_le['LE60_2020'] - m_le['LE60_2000']

df_prosp = pd.merge(df_2020_master[['Location', 'MedianAgePop', 'Region']], m_le, on='Location').dropna()
# Functional prospective median age = Chronological Median Age - dLE60
df_prosp['ProspectiveMedianAge'] = df_prosp['MedianAgePop'] - df_prosp['dLE60']

fig, ax = plt.subplots(figsize=(8.0, 4.8), dpi=300)
fig.patch.set_facecolor('#FFFFFF')
ax.set_facecolor('#FFFFFF')

# 45-degree line (Parity: Chronological = Prospective)
line_pts = np.linspace(14, 49, 100)
ax.plot(line_pts, line_pts, linestyle='--', color='#DC2626', linewidth=1.5, alpha=0.85, label='45° Parity Line (Zero Longevity Adjustment)', zorder=2)

# Scatter
regions = df_prosp['Region'].unique()
for r in regions:
    sub = df_prosp[df_prosp['Region'] == r]
    c = palette_map.get(r, '#64748B')
    ax.scatter(sub['MedianAgePop'], sub['ProspectiveMedianAge'], color=c, s=42, alpha=0.80, edgecolors='#FFFFFF', linewidths=0.6, label=r, zorder=3)

# Highlight the Longevity Dividend Zone (Shaded area under parity line)
ax.fill_between(line_pts, line_pts, line_pts - 2.5, color='#0284C7', alpha=0.08, label='Longevity Expansion Dividend (Functional Age < Chronological)')

# Annotate specific notable economies
callouts = [
    ('Japan', 48.4, 46.2, 49.0, 44.5),
    ('Italy', 47.3, 45.4, 47.8, 43.5),
    ('Germany', 45.9, 44.1, 46.5, 42.0),
    ('South Korea', 43.7, 40.8, 44.5, 39.0),
    ('Chile', 35.5, 33.2, 36.5, 31.5)
]
for name, cx, px, tx, ty in callouts:
    match = df_prosp[df_prosp['Location'] == name]
    if len(match) > 0:
        actual_cx = match['MedianAgePop'].values[0]
        actual_px = match['ProspectiveMedianAge'].values[0]
        ax.annotate(
            f"{name} (-{actual_cx - actual_px:.1f}y)",
            xy=(actual_cx, actual_px),
            xytext=(tx, ty),
            fontsize=7.8,
            fontweight='bold',
            color='#0F172A',
            arrowprops=dict(arrowstyle='->', color='#475569', lw=0.8, shrinkA=2, shrinkB=2)
        )

ax.set_xlabel('Nominal Chronological Median Age (Years, 2020)', fontsize=10.0, fontweight='bold', color='#0F172A', labelpad=8)
ax.set_ylabel('Prospective Median Age (Adjusted for LE60 Gains)', fontsize=10.0, fontweight='bold', color='#0F172A', labelpad=8)
ax.set_xlim(13.0, 51.0)
ax.set_ylim(11.0, 49.0)

ax.yaxis.grid(True, linestyle='-', linewidth=0.6, color='#E2E8F0', alpha=0.8, zorder=0)
ax.xaxis.grid(True, linestyle='-', linewidth=0.6, color='#E2E8F0', alpha=0.8, zorder=0)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#CBD5E1')
ax.spines['bottom'].set_color('#CBD5E1')

ax.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', fontsize=7.5)

plt.tight_layout()
plt.savefig('figures_v2/fig4_prospective_v2.png', dpi=300, facecolor='#FFFFFF', bbox_inches='tight')
plt.close()
# ==============================================================================
# FIGURE 6: 3-EPOCH GLOBAL DEMOGRAPHIC WAVE MAP (Horizontal Strip)
# ==============================================================================
print("Generating Figure 6: Horizontal 3-Epoch Global Demographic Wave Map...")

geojson_path = 'materials/world-countries.json'
metrics_csv = 'asymmetric_wave_country_metrics.csv'

with open(geojson_path, 'r', encoding='utf-8') as f:
    world_geo = json.load(f)

df_metrics = pd.read_csv(metrics_csv).set_index('ISO3_code')

# Color map:
# 0: Youthful (< 20.5y) -> #F59E0B (Warm Amber)
# 1: Transitioning (20.5 - 29.8y) -> #0284C7 (Cyan / Sky Blue)
# 2: Mature / Older (> 29.8y) -> #0F172A (Deep Slate / Navy)
# -1: Excluded / Missing -> #F1F5F9 (Ultra light slate)

c_map = {
    0: '#F59E0B',
    1: '#0284C7',
    2: '#0F172A',
    -1: '#F1F5F9'
}

epochs = [
    ("Epoch 1: 2000 Baseline", "Cluster_2000"),
    ("Epoch 2: 2020 Midpoint", "Cluster_2020"),
    ("Epoch 3: 2040 Frontier", "Cluster_2040")
]

fig, axes = plt.subplots(1, 3, figsize=(16.5, 3.4), dpi=300)
plt.subplots_adjust(wspace=0.02, left=0.01, right=0.99, top=0.88, bottom=0.14)

for idx, (title, col) in enumerate(epochs):
    ax = axes[idx]
    ax.set_title(title, fontsize=12.0, fontweight='bold', pad=8, color='#0F172A')
    ax.set_xlim(-180, 180)
    ax.set_ylim(-58, 83)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Draw countries
    for feat in world_geo['features']:
        iso3 = feat['id']
        geom_type = feat['geometry']['type']
        coords = feat['geometry']['coordinates']
        
        c_val = -1
        if iso3 in df_metrics.index:
            c_val = df_metrics.loc[iso3, col]
        
        fill_c = c_map.get(c_val, '#F1F5F9')
        edge_c = '#94A3B8' if c_val != -1 else '#CBD5E1'
        lw = 0.35 if c_val != -1 else 0.25
        
        if geom_type == 'Polygon':
            pts_list = [coords]
        elif geom_type == 'MultiPolygon':
            pts_list = coords
        else:
            continue
            
        for poly in pts_list:
            for ring in poly:
                ring_np = np.array(ring)
                if len(ring_np) >= 3:
                    polygon = patches.Polygon(ring_np, closed=True, facecolor=fill_c, edgecolor=edge_c, linewidth=lw, zorder=2)
                    ax.add_patch(polygon)

# Shared legend at bottom
legend_elements = [
    patches.Patch(facecolor='#F59E0B', edgecolor='#94A3B8', label='Youthful (Median Age < 20.5y)'),
    patches.Patch(facecolor='#0284C7', edgecolor='#94A3B8', label='Transitioning (20.5 – 29.8y)'),
    patches.Patch(facecolor='#0F172A', edgecolor='#94A3B8', label='Mature / Older (> 29.8y)'),
    patches.Patch(facecolor='#F1F5F9', edgecolor='#CBD5E1', label='Excluded (< 1M Pop or Non-Sovereign)')
]

fig.legend(handles=legend_elements, loc='lower center', ncol=4, frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, 0.02))

plt.savefig('figures_v2/fig6_map_strip_v2.png', dpi=300, facecolor='#FFFFFF', bbox_inches='tight')
plt.close()
print("Figure 6 saved.")

print("All bespoke figures generated successfully.")

