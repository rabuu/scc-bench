from pathlib import Path

import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl


# ============================================================
# Configuration
# ============================================================

VERSIONS = ["main", "lin", "sf"]
BASELINE = "main"

COLORS = {
    "main": "#D0021B",
    "lin": "#56B4E9",
    "sf": "#fff600",
}

# SVG config
mpl.rcParams.update({
    "font.size": 15,
    "axes.titlesize": 15,
    "axes.labelsize": 15,
    "xtick.labelsize": 13,
    "ytick.labelsize": 15,
    "legend.fontsize": 15,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "font.family": "Libertinus Sans",
    "svg.fonttype": "none",
})


# ============================================================
# Read CSV files
# ============================================================

rows = []

for csv in Path("./results/raw").glob("*.csv"):
    benchmark = csv.stem

    df = pl.read_csv(csv).select(["command", "mean", "stddev"])

    # Dynamically detect version from executable suffix
    variant_expr = pl.lit(None, dtype=pl.String)

    for version in VERSIONS:
        variant_expr = (
            pl.when(
                pl.col("command").str.contains(
                    rf"_{version}(\s|$)"
                )
            )
            .then(pl.lit(version))
            .otherwise(variant_expr)
        )

    df = (
        df
        .with_columns(
            pl.lit(benchmark).alias("benchmark"),
            variant_expr.alias("variant"),
        )
        .filter(pl.col("variant").is_not_null())
    )

    rows.append(df)

df = pl.concat(rows)


# ============================================================
# Pivot results
# ============================================================

results = (
    df
    .pivot(
        values=["mean", "stddev"],
        index="benchmark",
        on="variant",
    )
)

# Normalize means and standard deviations against baseline
for version in VERSIONS:
    results = results.with_columns(
        (
            pl.col(f"mean_{version}")
            / pl.col(f"mean_{BASELINE}")
        ).alias(f"normalized_{version}"),

        (
            pl.col(f"stddev_{version}")
            / pl.col(f"mean_{BASELINE}")
        ).alias(f"normalized_stddev_{version}"),
    )


# ============================================================
# Table output
# ============================================================

print("Normalized execution times and speedups:\n")

for row in results.sort("benchmark").iter_rows(named=True):
    values = ", ".join(
        (
            f"{version}: "
            f"{row[f'normalized_{version}']:.3f} "
            f"({1.0 / row[f'normalized_{version}']:.3f}×)"
        )
        for version in VERSIONS
    )

    print(f"`{row['benchmark']}`, {values}")


# ============================================================
# Plot
# ============================================================

# Sort benchmarks by performance of the last configured version
plot_res = results.sort(
    f"normalized_{VERSIONS[-1]}"
)

benchmarks = plot_res["benchmark"].to_list()

n_versions = len(VERSIONS)
spacing = 1.3

y = np.arange(len(benchmarks)) * spacing
bar_h = spacing * 0.8 / n_versions

fig, ax = plt.subplots(
    figsize=(12, max(6, len(benchmarks) * 0.45))
)

# Collect normalized means and errors
all_means = {
    version: plot_res[f"normalized_{version}"].to_list()
    for version in VERSIONS
}

all_errors = {
    version: plot_res[f"normalized_stddev_{version}"].to_list()
    for version in VERSIONS
}

# Calculate maximum bar extent
global_max = max(
    mean + error
    for version in VERSIONS
    for mean, error in zip(
        all_means[version],
        all_errors[version],
    )
)

x_offset = global_max * 0.025

# Plot all versions
for i, version in enumerate(VERSIONS):
    means = all_means[version]
    errors = all_errors[version]

    offset = (i - (n_versions - 1) / 2) * bar_h

    ax.barh(
        y + offset,
        means,
        height=bar_h,
        color=COLORS[version],
        label=version,
        xerr=errors,
        capsize=2,
    )

    # Speedup labels relative to baseline
    for j, (mean, error) in enumerate(zip(means, errors)):
        speedup = 1.0 / mean

        ax.text(
            mean + error + x_offset,
            y[j] + offset,
            f"{speedup:.2f}×",
            va="center",
            ha="left",
            fontsize=12,
            fontweight="bold",
            color="black",
        )


# ============================================================
# Plot formatting
# ============================================================

ax.set_yticks(y, benchmarks)

ax.set_xlabel(
    f"Normalized execution time (1.0 = {BASELINE})"
)

ax.invert_yaxis()

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Legend outside plotting area
ax.legend(
    frameon=False,
    loc="center left",
    bbox_to_anchor=(1.02, 0.5),
)

ax.grid(
    axis="x",
    linestyle="--",
    alpha=0.3,
)

ax.tick_params(axis="y", pad=6)

# Leave room for speedup labels
ax.set_xlim(right=global_max * 1.25)

plt.tight_layout(rect=[0, 0, 0.85, 1])

plt.savefig(
    "runtime.svg",
    bbox_inches="tight",
)

plt.show()
