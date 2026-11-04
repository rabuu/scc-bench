from pathlib import Path

import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl


# ============================================================
# Configuration
# ============================================================

VERSIONS = ["main", "lin", "sf1", "sf2", "sf3", "sf4"]
BASELINE = "main"

COLORS = {
    "main": "#D0021B",
    "lin":  "#56B4E9",
    "sf1":  "#E69F00",
    "sf2":  "#009E73",
    "sf3":  "#CC79A7",
    "sf4":  "#0072B2",
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

from matplotlib.ticker import NullLocator

# Same order as before: biggest speedup of the last version at the top
plot_res = results.sort(f"normalized_{VERSIONS[-1]}")
benchmarks = plot_res["benchmark"].to_list()

compared = [v for v in VERSIONS if v != BASELINE]
n = len(compared)

y = np.arange(len(benchmarks))
row_h = 0.32          # inches per benchmark row
fig, ax = plt.subplots(figsize=(10, max(6, len(benchmarks) * row_h + 1.5)))

# Zebra striping makes it easy to follow a row across the plot
for k in range(0, len(benchmarks), 2):
    ax.axhspan(k - 0.5, k + 0.5, color="0.95", zorder=0)

# Baseline
ax.axvline(1.0, color=COLORS[BASELINE], lw=1.5, zorder=1, label=BASELINE)

spread = 0.7          # fraction of a row used by the dots
for i, version in enumerate(compared):
    norm = np.array(plot_res[f"normalized_{version}"].to_list())
    norm_err = np.array(plot_res[f"normalized_stddev_{version}"].to_list())

    speedup = 1.0 / norm
    speedup_err = speedup * norm_err / norm   # error propagation for 1/x

    offset = (i - (n - 1) / 2) * spread / n

    ax.errorbar(
        speedup,
        y + offset,
        xerr=speedup_err,
        fmt="o",
        ms=4.5,
        color=COLORS[version],
        ecolor=COLORS[version],
        elinewidth=1,
        capsize=0,
        label=version,
        zorder=3,
    )

# ============================================================
# Plot formatting
# ============================================================

ax.set_xscale("log", base=2)
ticks = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 3]
ax.set_xticks(ticks)
ax.set_xticklabels([f"{t:g}×" for t in ticks])
ax.xaxis.set_minor_locator(NullLocator())

ax.set_yticks(y, benchmarks)
ax.set_ylim(len(benchmarks) - 0.5, -0.5)   # top-to-bottom, no invert_yaxis needed

ax.set_xlabel(f"Speedup over {BASELINE} (higher is better, log scale)")

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(axis="x", linestyle="--", alpha=0.3)
ax.tick_params(axis="y", length=0, pad=6)

ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.02, 0.5))

plt.tight_layout()
plt.savefig("dotplot.svg", bbox_inches="tight")
plt.show()
