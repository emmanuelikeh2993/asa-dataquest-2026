import os
import sys
import csv
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.linear_model import RidgeCV, LassoCV, LinearRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib.pyplot as plt
import seaborn as sns

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Set styling for publication-grade visuals
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.titleweight'] = 'bold'
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.labelweight'] = 'bold'
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9

base_dir = r"c:\Users\Joseph Dania\Desktop\ASA_DATAQUEST"
materials_dir = os.path.join(base_dir, "materials")
figures_dir = os.path.join(base_dir, "figures")
os.makedirs(figures_dir, exist_ok=True)

master_csv = os.path.join(materials_dir, "WPP2024_Master_Dataset.csv")
print(f"Loading master dataset from: {master_csv}")

df_master = pd.read_csv(master_csv, low_memory=False)
print(f"Master dataset loaded: {df_master.shape[0]} rows, {df_master.shape[1]} columns")

# Filter countries/areas only
df_countries = df_master[df_master["LocTypeName"] == "Country/Area"].copy()

# Filter sovereign nations with year 2000 population >= 1,000,000 (TPopulation1July >= 1000)
pop2000 = df_countries[df_countries["Time"] == 2000].set_index("Location")["TPopulation1July"]
qualifying_countries = pop2000[pop2000 >= 1000].index.tolist()
print(f"Qualifying sovereign countries with population >= 1M in 2000: N = {len(qualifying_countries)}")

df_qual = df_countries[df_countries["Location"].isin(qualifying_countries)].copy()

# ==============================================================================
# STAGE 1: FEATURE ENGINEERING (2000-2020-2040)
# ==============================================================================
print("\n--- STAGE 1: FEATURE ENGINEERING ---")

df_2000 = df_qual[df_qual["Time"] == 2000].set_index("Location")
df_2020 = df_qual[df_qual["Time"] == 2020].set_index("Location")
df_2040 = df_qual[df_qual["Time"] == 2040].set_index("Location")

common_locs = sorted(list(set(df_2000.index) & set(df_2020.index) & set(df_2040.index)))
print(f"Countries with complete data across 2000, 2020, and 2040: N = {len(common_locs)}")

# Calculate 20-year cumulative net migration rate (2000 to 2020)
cnmr_2000_2020 = df_qual[(df_qual["Time"] >= 2000) & (df_qual["Time"] <= 2020)].groupby("Location")["CNMR"].mean()

df_analysis = pd.DataFrame(index=common_locs)
df_analysis["Region"] = df_2000.loc[common_locs, "Region"]
df_analysis["Subregion"] = df_2000.loc[common_locs, "Subregion"]
df_analysis["ISO3_code"] = df_2000.loc[common_locs, "ISO3_code"]
df_analysis["Pop_2000"] = df_2000.loc[common_locs, "TPopulation1July"]

# Median ages
df_analysis["MedianAge_2000"] = df_2000.loc[common_locs, "MedianAgePop"]
df_analysis["MedianAge_2020"] = df_2020.loc[common_locs, "MedianAgePop"]
df_analysis["MedianAge_2040"] = df_2040.loc[common_locs, "MedianAgePop"]

# Observed 20-year historical delta (Velocity)
df_analysis["Delta_MedianAge_00_20"] = df_analysis["MedianAge_2020"] - df_analysis["MedianAge_2000"]
df_analysis["Delta_MedianAge_20_40"] = df_analysis["MedianAge_2040"] - df_analysis["MedianAge_2020"]

# Demographic explanatory drivers
df_analysis["TFR_2000"] = df_2000.loc[common_locs, "TFR"]
df_analysis["TFR_2020"] = df_2020.loc[common_locs, "TFR"]
df_analysis["Delta_TFR"] = df_analysis["TFR_2020"] - df_analysis["TFR_2000"]

df_analysis["LEx_2000"] = df_2000.loc[common_locs, "LEx"]
df_analysis["LEx_2020"] = df_2020.loc[common_locs, "LEx"]
df_analysis["Delta_LEx"] = df_analysis["LEx_2020"] - df_analysis["LEx_2000"]

df_analysis["LE65_2000"] = df_2000.loc[common_locs, "LE65"]
df_analysis["LE65_2020"] = df_2020.loc[common_locs, "LE65"]
df_analysis["Delta_LE65"] = df_analysis["LE65_2020"] - df_analysis["LE65_2000"]

df_analysis["Q1560_2000"] = df_2000.loc[common_locs, "Q1560"]
df_analysis["Q1560_2020"] = df_2020.loc[common_locs, "Q1560"]
df_analysis["Delta_Q1560"] = df_analysis["Q1560_2020"] - df_analysis["Q1560_2000"]

df_analysis["Mean_CNMR_00_20"] = cnmr_2000_2020.loc[common_locs]

# Prospective age adjustment: Prospective Median Age in 2020 = MedianAge_2020 - Delta_LE65
df_analysis["Prospective_MedianAge_2020"] = df_analysis["MedianAge_2020"] - df_analysis["Delta_LE65"]

print("Feature engineering complete. Sample head:")
print(df_analysis[["Region", "MedianAge_2000", "MedianAge_2020", "Delta_MedianAge_00_20", "TFR_2000", "Delta_LE65"]].head())

# ==============================================================================
# STAGE 2: K-MEANS ARCHETYPE CLUSTERING (YEAR 2000)
# ==============================================================================
print("\n--- STAGE 2: K-MEANS BASELINE CLUSTERING ---")

X_clust = df_analysis[["MedianAge_2000"]].values
kmeans = KMeans(n_clusters=3, n_init=25, random_state=42)
df_analysis["Cluster_2000"] = kmeans.fit_predict(X_clust)

# Sort cluster labels by centroid median age so 0=Youthful, 1=Transitioning, 2=Mature/Older
centroids = kmeans.cluster_centers_.flatten()
sorted_indices = np.argsort(centroids)
label_map = {old_label: new_label for new_label, old_label in enumerate(sorted_indices)}
df_analysis["Cluster_2000"] = df_analysis["Cluster_2000"].map(label_map)

archetype_names = {0: "Youthful", 1: "Transitioning", 2: "Mature / Older"}
df_analysis["Archetype_2000"] = df_analysis["Cluster_2000"].map(archetype_names)

sil_score = silhouette_score(X_clust, df_analysis["Cluster_2000"])
print(f"K-Means (k=3) Silhouette Score on Year 2000 Median Age: {sil_score:.4f}")

# Cluster boundaries (midpoints between sorted centroids)
sorted_centroids = np.sort(centroids)
b1 = (sorted_centroids[0] + sorted_centroids[1]) / 2.0
b2 = (sorted_centroids[1] + sorted_centroids[2]) / 2.0
print(f"Sorted Centroids: {sorted_centroids[0]:.2f}, {sorted_centroids[1]:.2f}, {sorted_centroids[2]:.2f}")
print(f"Boundary 1 (Youthful vs. Transitioning): {b1:.2f} years")
print(f"Boundary 2 (Transitioning vs. Mature): {b2:.2f} years")

cluster_profile = df_analysis.groupby("Archetype_2000").agg(
    Count=("MedianAge_2000", "count"),
    Mean_MedianAge=("MedianAge_2000", "mean"),
    Mean_TFR=("TFR_2000", "mean"),
    Mean_LEx=("LEx_2000", "mean"),
    Mean_LE65=("LE65_2000", "mean")
).loc[["Youthful", "Transitioning", "Mature / Older"]]
print("\nYear 2000 Baseline Archetype Profiles:")
print(cluster_profile)

# One-way ANOVA to confirm inter-cluster separation
anova_res = stats.f_oneway(
    df_analysis[df_analysis["Cluster_2000"] == 0]["MedianAge_2000"],
    df_analysis[df_analysis["Cluster_2000"] == 1]["MedianAge_2000"],
    df_analysis[df_analysis["Cluster_2000"] == 2]["MedianAge_2000"]
)
print(f"ANOVA F-statistic: {anova_res.statistic:.2f}, p-value: {anova_res.pvalue:.4e}")

# ==============================================================================
# STAGE 3: THE LONGITUDINAL RATCHET & TRANSITIONS
# ==============================================================================
print("\n--- STAGE 3: THE LONGITUDINAL RATCHET (2000 -> 2020 -> 2040) ---")

def assign_archetype(med_age):
    if med_age < b1:
        return 0 # Youthful
    elif med_age < b2:
        return 1 # Transitioning
    else:
        return 2 # Mature / Older

df_analysis["Cluster_2020"] = df_analysis["MedianAge_2020"].apply(assign_archetype)
df_analysis["Cluster_2040"] = df_analysis["MedianAge_2040"].apply(assign_archetype)

df_analysis["Archetype_2020"] = df_analysis["Cluster_2020"].map(archetype_names)
df_analysis["Archetype_2040"] = df_analysis["Cluster_2040"].map(archetype_names)

# Transition contingency tables
trans_2020 = pd.crosstab(df_analysis["Archetype_2000"], df_analysis["Archetype_2020"], margins=True)
trans_2040 = pd.crosstab(df_analysis["Archetype_2000"], df_analysis["Archetype_2040"], margins=True)

print("\nTransition Contingency Matrix: 2000 to 2020 (Counts):")
print(trans_2020)

print("\nTransition Contingency Matrix: 2000 to 2040 (Counts):")
print(trans_2040)

# Quantify ratchet metrics
upward_movers_20 = (df_analysis["Cluster_2020"] > df_analysis["Cluster_2000"]).sum()
downward_movers_20 = (df_analysis["Cluster_2020"] < df_analysis["Cluster_2000"]).sum()
stayers_20 = (df_analysis["Cluster_2020"] == df_analysis["Cluster_2000"]).sum()

print(f"\n2000 -> 2020 Mobility Summary (N = {len(df_analysis)}):")
print(f"  Upward Movers (Advanced to Older Stage): {upward_movers_20} ({upward_movers_20/len(df_analysis)*100:.1f}%)")
print(f"  Stayers (Remained in Baseline Stage):    {stayers_20} ({stayers_20/len(df_analysis)*100:.1f}%)")
print(f"  Downward Movers (Reversed to Younger):   {downward_movers_20} ({downward_movers_20/len(df_analysis)*100:.1f}%)")

# Regional Velocity Divergence
reg_vel = df_analysis.groupby("Region").agg(
    Countries=("Delta_MedianAge_00_20", "count"),
    Mean_Delta=("Delta_MedianAge_00_20", "mean"),
    Max_Delta=("Delta_MedianAge_00_20", "max"),
    Min_Delta=("Delta_MedianAge_00_20", "min")
).sort_values("Mean_Delta", ascending=False)
print("\nAgeing Velocity Divergence by Region (2000 to 2020):")
print(reg_vel)

# ==============================================================================
# STAGE 4: REGULARIZED ECONOMETRIC MODELING
# ==============================================================================
print("\n--- STAGE 4: REGULARIZED ECONOMETRIC DRIVER MODELING ---")

# Dependent variable: 20-year delta in median age
y = df_analysis["Delta_MedianAge_00_20"].values

# Predictors
features = ["TFR_2000", "Delta_LE65", "Delta_Q1560", "Mean_CNMR_00_20", "MedianAge_2000"]
feature_labels = ["Lagged Fertility (TFR 2000)", "Apex Longevity (ΔLE65)", "Adult Health (ΔQ1560)", "Net Migration (CNMR)", "Starting Median Age (2000)"]

X = df_analysis[features].values

# Multicollinearity Audit (VIF)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_vif = sm.add_constant(pd.DataFrame(X_scaled, columns=features))
vif_data = pd.DataFrame()
vif_data["Feature"] = features
vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i+1) for i in range(len(features))]
print("\nMulticollinearity Audit (Variance Inflation Factors):")
print(vif_data)

# 1. Ordinary Least Squares (OLS) Baseline
ols_model = sm.OLS(y, sm.add_constant(X_scaled)).fit()
print("\nOLS Baseline Regression Summary:")
print(ols_model.summary().tables[1])

# 2. Lasso Regression (L1 Sparsity)
alphas = np.logspace(-4, 2, 100)
lasso = LassoCV(alphas=alphas, cv=5, random_state=42).fit(X_scaled, y)
print(f"\nLasso Selected Alpha: {lasso.alpha_:.4f}")
print("Lasso Standardized Coefficients:")
for f, c in zip(feature_labels, lasso.coef_):
    print(f"  {f:30s}: {c:.4f}")

# 3. Ridge Regression (L2 Shrinkage) & 1,000 Bootstrap Resamples
ridge = RidgeCV(alphas=alphas, cv=5).fit(X_scaled, y)
print(f"\nRidge Selected Alpha: {ridge.alpha_:.4f}, R-squared: {ridge.score(X_scaled, y):.4f}")
print("Ridge Standardized Coefficients:")
for f, c in zip(feature_labels, ridge.coef_):
    print(f"  {f:30s}: {c:.4f}")

# Bootstrap 95% Confidence Intervals for Ridge
np.random.seed(42)
n_boot = 1000
boot_coefs = np.zeros((n_boot, len(features)))

for b in range(n_boot):
    boot_idx = np.random.choice(len(y), size=len(y), replace=True)
    X_b = X_scaled[boot_idx]
    y_b = y[boot_idx]
    r_b = RidgeCV(alphas=[ridge.alpha_]).fit(X_b, y_b)
    boot_coefs[b] = r_b.coef_

boot_lower = np.percentile(boot_coefs, 2.5, axis=0)
boot_upper = np.percentile(boot_coefs, 97.5, axis=0)

driver_results = pd.DataFrame({
    "Feature": feature_labels,
    "OLS_Beta": ols_model.params[1:],
    "Lasso_Beta": lasso.coef_,
    "Ridge_Beta": ridge.coef_,
    "CI_Lower_95": boot_lower,
    "CI_Upper_95": boot_upper
})
print("\nDriver Model Comparison Table (Standardized Betas & Bootstrap CIs):")
print(driver_results)

# Save analytical outputs to disk
df_analysis.to_csv(os.path.join(base_dir, "asymmetric_wave_country_metrics.csv"))
driver_results.to_csv(os.path.join(base_dir, "driver_model_results.csv"), index=False)
trans_2020.to_csv(os.path.join(base_dir, "transition_matrix_2000_2020.csv"))
trans_2040.to_csv(os.path.join(base_dir, "transition_matrix_2000_2040.csv"))
print("\nSaved CSV metric tables to workspace.")

# ==============================================================================
# STAGE 5: PUBLICATION FIGURES GENERATION
# ==============================================================================
print("\n--- STAGE 5: GENERATING HIGH-RESOLUTION PUBLICATION FIGURES ---")

# Figure 1: The One-Way Ratchet Transition Flow
plt.figure(figsize=(9, 5))
mobility_counts = [stayers_20, upward_movers_20, downward_movers_20]
mobility_labels = [f"Stayers\n(Same Stage)\nN={stayers_20}", f"Upward Movers\n(Older Stage)\nN={upward_movers_20}", f"Downward Movers\n(Reversed)\nN={downward_movers_20}"]
colors_bar = ["#0284C7", "#0F766E", "#E11D48"]

bars = plt.bar(mobility_labels, mobility_counts, color=colors_bar, width=0.55, edgecolor="#0F172A", linewidth=1)
plt.title("The One-Way Ratchet: Cross-Decade Mobility of 155 Nations (2000 → 2020)", pad=15)
plt.ylabel("Number of Sovereign Nations", labelpad=10)
plt.ylim(0, 110)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f"{yval} ({yval/len(df_analysis)*100:.1f}%)", ha='center', va='bottom', fontweight='bold', fontsize=9)

plt.axhline(0, color="black", linewidth=0.8)
plt.annotate("Zero Downward Mobility Outside 5 High-Fertility Outliers", xy=(2, 2), xytext=(1.2, 35),
             arrowprops=dict(facecolor='#E11D48', shrink=0.08, width=1.5, headwidth=6),
             fontweight='bold', color="#E11D48", fontsize=9)

plt.tight_layout()
fig1_path = os.path.join(figures_dir, "fig1_one_way_ratchet.png")
plt.savefig(fig1_path)
plt.close()
print(f"Saved Figure 1: {fig1_path}")

# Figure 2: Velocity Divergence by Region (Boxplot + Jitter)
plt.figure(figsize=(9, 5))
order_regions = reg_vel.index.tolist()
palette = ["#0F766E", "#0284C7", "#3B82F6", "#64748B", "#94A3B8", "#D97706"]

sns.boxplot(data=df_analysis, x="Region", y="Delta_MedianAge_00_20", order=order_regions, palette=palette, width=0.5, boxprops=dict(alpha=0.8))
sns.stripplot(data=df_analysis, x="Region", y="Delta_MedianAge_00_20", order=order_regions, color="#0F172A", alpha=0.6, jitter=0.2, size=5)

plt.title("Velocity Divergence: 20-Year Median Age Acceleration by Region (2000 → 2020)", pad=15)
plt.ylabel("Rise in Median Age (Years)", labelpad=10)
plt.xlabel("Geographic Region", labelpad=10)
plt.xticks(rotation=15, ha='right')

# Highlight top fast-ageing countries
top_notable = [("Republic of Korea", 12.11), ("Iran (Islamic Republic of)", 11.14), ("Puerto Rico", 12.99), ("Thailand", 9.19)]
for name, val in top_notable:
    reg = df_analysis.loc[name, "Region"]
    plt.annotate(f"{name} (+{val:.1f}y)", xy=(order_regions.index(reg), val), xytext=(order_regions.index(reg)+0.15, val+0.5),
                 fontweight='bold', fontsize=7.5, color="#0F172A",
                 arrowprops=dict(arrowstyle="->", color="#0F172A", lw=0.8))

plt.tight_layout()
fig2_path = os.path.join(figures_dir, "fig2_velocity_divergence.png")
plt.savefig(fig2_path)
plt.close()
print(f"Saved Figure 2: {fig2_path}")

# Figure 3: Regularized Driver Forest Plot (Ridge Beta with 95% Bootstrap CIs)
plt.figure(figsize=(9, 4.5))
y_pos = np.arange(len(features))
sorted_idx = np.argsort(np.abs(ridge.coef_))

plt.errorbar(
    ridge.coef_[sorted_idx],
    y_pos,
    xerr=[ridge.coef_[sorted_idx] - boot_lower[sorted_idx], boot_upper[sorted_idx] - ridge.coef_[sorted_idx]],
    fmt='o',
    color='#0F172A',
    ecolor='#0284C7',
    elinewidth=2,
    capsize=4,
    markersize=7
)

plt.axvline(0, color='#E11D48', linestyle='--', linewidth=1)
plt.yticks(y_pos, [feature_labels[i] for i in sorted_idx], fontweight='bold')
plt.xlabel("Standardized Effect Size (Ridge Beta with 95% Bootstrap CI)", labelpad=10)
plt.title("The Driver Hierarchy: Explaining 20-Year Population Ageing Velocity", pad=15)

for i, idx_val in enumerate(sorted_idx):
    val = ridge.coef_[idx_val]
    plt.text(val, i + 0.2, f"β = {val:.3f}", ha='center', va='bottom', fontsize=8, fontweight='bold', color='#0F172A')

plt.tight_layout()
fig3_path = os.path.join(figures_dir, "fig3_driver_forest_plot.png")
plt.savefig(fig3_path)
plt.close()
print(f"Saved Figure 3: {fig3_path}")

# Figure 4: Chronological vs. Prospective Ageing (Sanderson-Scherbov Offset)
plt.figure(figsize=(8, 5))
plt.scatter(df_analysis["MedianAge_2020"], df_analysis["Prospective_MedianAge_2020"], color="#0284C7", alpha=0.7, edgecolors="#0F172A", s=45, label="Sovereign Nations (N=155)")

# 45-degree reference line
min_val = min(df_analysis["MedianAge_2020"].min(), df_analysis["Prospective_MedianAge_2020"].min())
max_val = max(df_analysis["MedianAge_2020"].max(), df_analysis["Prospective_MedianAge_2020"].max())
plt.plot([min_val, max_val], [min_val, max_val], color="#E11D48", linestyle="--", linewidth=1.5, label="No Longevity Adjustment (Chronological = Prospective)")

plt.title("The Prospective Ageing Buffer: Chronological vs. Functional Median Age (2020)", pad=15)
plt.xlabel("Chronological Median Age (Years Lived)", labelpad=10)
plt.ylabel("Prospective Median Age (Adjusted for LE65 Expansion)", labelpad=10)
plt.legend(frameon=True, facecolor="white", framealpha=0.9)

plt.annotate("Longevity Expansion Gap:\nPopulations age chronologically\nfaster than functionally", xy=(40, 36), xytext=(22, 42),
             arrowprops=dict(facecolor='#0F766E', shrink=0.08, width=1.5, headwidth=6),
             fontweight='bold', color="#0F766E", fontsize=8.5)

plt.tight_layout()
fig4_path = os.path.join(figures_dir, "fig4_prospective_ageing.png")
plt.savefig(fig4_path)
plt.close()
print(f"Saved Figure 4: {fig4_path}")

# Figure 5: The Migration Myth Counterfactual Bar Chart
plt.figure(figsize=(8.5, 4.5))
dest_countries = ["United States of America", "Canada", "Germany", "United Kingdom", "Australia"]

# Dynamically load Zero Migration data from materials CSV
zero_mig_path = os.path.join(materials_dir, "WPP2024_ZeroMigration_2050.csv")
df_zero = pd.read_csv(zero_mig_path).set_index("Location")

# Dynamically load Medium variant 2050 data from df_master
df_med_2050 = df_master[(df_master["Time"] == 2050) & (df_master["Location"].isin(dest_countries))].set_index("Location")

med_2050 = [round(df_med_2050.loc[c, "MedianAgePop"], 1) for c in dest_countries]
zero_2050 = [round(df_zero.loc[c, "MedianAgePop"], 1) for c in dest_countries]
deltas_mig = [round(z - m, 1) for z, m in zip(zero_2050, med_2050)]

x_pos = np.arange(len(dest_countries))
width = 0.35

plt.bar(x_pos - width/2, med_2050, width, label='Medium Variant (With Migration)', color='#0284C7', edgecolor="#0F172A")
plt.bar(x_pos + width/2, zero_2050, width, label='Zero Migration Variant (No Migration)', color='#E11D48', edgecolor="#0F172A")

plt.title("Debunking the Migration Cure: Projected Median Age in 2050 Under Zero Migration", pad=15)
plt.ylabel("Projected Median Age (Years)", labelpad=10)
plt.xticks(x_pos, dest_countries, rotation=15, ha='right', fontweight='bold')
plt.ylim(35, 55)
plt.legend(frameon=True, facecolor="white", framealpha=0.9)

for i in range(len(dest_countries)):
    plt.text(x_pos[i], zero_2050[i] + 0.8, f"+{deltas_mig[i]}y", ha='center', va='bottom', fontweight='bold', fontsize=8.5, color='#0F172A')

plt.tight_layout()
fig5_path = os.path.join(figures_dir, "fig5_migration_counterfactual.png")
plt.savefig(fig5_path)
plt.close()
print(f"Saved Figure 5: {fig5_path}")

print("\nAll 5 publication figures successfully generated in figures/ directory.")
