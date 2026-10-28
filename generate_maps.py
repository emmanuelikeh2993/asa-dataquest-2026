import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import ListedColormap
import matplotlib.patches as mpatches

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base_dir = r"c:\Users\Joseph Dania\Desktop\ASA_DATAQUEST"
materials_dir = os.path.join(base_dir, "materials")
figures_dir = os.path.join(base_dir, "figures")
geojson_path = os.path.join(materials_dir, "world-countries.json")
metrics_csv = os.path.join(base_dir, "asymmetric_wave_country_metrics.csv")

with open(geojson_path, "r", encoding="utf-8") as f:
    world_geo = json.load(f)

df_metrics = pd.read_csv(metrics_csv).set_index("ISO3_code")

# Palette for the 3 archetypes:
# 0: Youthful (Median Age < 20.5) -> #E2E8F0 (light background) / #F59E0B (warm amber)
# 1: Transitioning (20.5 - 29.8) -> #0284C7 (vibrant cyan/blue)
# 2: Mature / Older (> 29.8) -> #0F172A (deep midnight navy)
color_map = {
    0: "#F59E0B",  # Youthful (Amber)
    1: "#0284C7",  # Transitioning (Cyan/Blue)
    2: "#0F172A",  # Mature / Older (Deep Navy)
    -1: "#E2E8F0"  # Missing / non-sovereign
}

epochs = [
    ("2000 (Baseline Epoch)", "Cluster_2000"),
    ("2020 (Observed Midpoint)", "Cluster_2020"),
    ("2040 (Projected Frontier)", "Cluster_2040")
]

fig, axes = plt.subplots(3, 1, figsize=(14, 18), dpi=300)
plt.subplots_adjust(hspace=0.15)

for idx, (title, col) in enumerate(epochs):
    ax = axes[idx]
    ax.set_title(title, fontsize=14, fontweight='bold', pad=10, color='#0F172A')
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 85)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Draw countries
    for feat in world_geo["features"]:
        iso3 = feat["id"]
        geom_type = feat["geometry"]["type"]
        coords = feat["geometry"]["coordinates"]
        
        # Determine color
        cluster_val = -1
        if iso3 in df_metrics.index and pd.notna(df_metrics.loc[iso3, col]):
            cluster_val = int(df_metrics.loc[iso3, col])
        fill_color = color_map[cluster_val]
        
        polys = []
        if geom_type == "Polygon":
            poly_coords = [coords[0]]
            for c in poly_coords:
                polys.append(Polygon(np.array(c), closed=True))
        elif geom_type == "MultiPolygon":
            for poly in coords:
                polys.append(Polygon(np.array(poly[0]), closed=True))
        
        p_col = PatchCollection(polys, facecolor=fill_color, edgecolor="#64748B", linewidth=0.35, alpha=0.95)
        ax.add_collection(p_col)

# Add master legend at bottom
legend_patches = [
    mpatches.Patch(facecolor="#F59E0B", edgecolor="#0F172A", label="Youthful Archetype (Median Age < 20.5 yrs)"),
    mpatches.Patch(facecolor="#0284C7", edgecolor="#0F172A", label="Transitioning Archetype (Median Age 20.5 – 29.8 yrs)"),
    mpatches.Patch(facecolor="#0F172A", edgecolor="#0F172A", label="Mature / Older Archetype (Median Age > 29.8 yrs)"),
    mpatches.Patch(facecolor="#E2E8F0", edgecolor="#94A3B8", label="Excluded (< 1M Pop or Non-Sovereign Area)")
]

fig.legend(handles=legend_patches, loc="lower center", ncol=2, fontsize=11, frameon=True, facecolor="white", edgecolor="#CBD5E1", bbox_to_anchor=(0.5, 0.02))

fig.suptitle("The Asymmetric Wave: Global Demographic Archetype Diffusion (2000 → 2020 → 2040)\nEmpirical Transition of 155 Sovereign Nations (UN WPP 2024)", fontsize=16, fontweight='bold', y=0.96, color='#0F172A')

out_map = os.path.join(figures_dir, "fig6_global_wave_maps.png")
plt.savefig(out_map, bbox_inches="tight")
plt.close()
print(f"Generated 3-map global choropleth: {out_map}")
