from pathlib import Path
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

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
    "svg.fonttype": "none",  # IMPORTANT: keeps text as text in SVG (best for Typst)
})

rows = []

for csv in Path("./results/raw").glob("*.csv"):
    benchmark = csv.stem

    df = (
        pl.read_csv(csv)
        .select(["command", "mean", "stddev"])
        .with_columns(
            pl.lit(benchmark).alias("benchmark"),
            pl.when(pl.col("command").str.contains("_lin"))
                .then(pl.lit("lin"))
                .when(pl.col("command").str.contains("_sf"))
                .then(pl.lit("sf"))
                .otherwise(pl.lit("main"))
                .alias("variant")
        )
    )

    rows.append(df)

df = pl.concat(rows)
# df = df.filter(~pl.col("benchmark").str.contains("Goto"))

# Columns: benchmark, mean_{main,lin,sf}, stddev_{main,lin,sf}
results = (
    df
    .pivot(
        values=["mean", "stddev"],
        index="benchmark",
        on="variant",
    )
    .with_columns(
        (pl.col("mean_main") / pl.col("mean_lin")).alias("speedup_lin"),
        (pl.col("mean_main") / pl.col("mean_sf")).alias("speedup_sf"),
    )
)

# Table output (alphabetical by benchmark)
for row in results.sort("benchmark").iter_rows(named=True):
    print(
        f"`{row['benchmark']}`, "
        f"[{row['mean_main']:.5f}s], "
        f"[{row['stddev_main']:.5f}s], "
        f"[{row['mean_lin']:.5f}s], "
        f"[{row['stddev_lin']:.5f}s], "
        f"[{row['speedup_lin']:.3f}], "
        f"[{row['mean_sf']:.5f}s], "
        f"[{row['stddev_sf']:.5f}s], "
        f"[{row['speedup_sf']:.3f}],"
    )

geomeans = results.select(
    pl.col("speedup_lin").log().mean().exp().alias("lin"),
    pl.col("speedup_sf").log().mean().exp().alias("sf"),
).row(0, named=True)

print(f"\nGeometric mean speedup (lin): {geomeans['lin']:.3f}×")
print(f"Geometric mean speedup (sf):  {geomeans['sf']:.3f}×")

# Plot order: by improvement of sf over main
plot_res = results.sort("speedup_sf", descending=True)
benchmarks = plot_res.get_column("benchmark").to_list()

main_means = plot_res["mean_main"].to_list()
lin_means = plot_res["mean_lin"].to_list()
sf_means = plot_res["mean_sf"].to_list()

main_err = plot_res["stddev_main"].to_list()
lin_err = plot_res["stddev_lin"].to_list()
sf_err = plot_res["stddev_sf"].to_list()

speedups_lin = plot_res["speedup_lin"].to_list()
speedups_sf = plot_res["speedup_sf"].to_list()

spacing = 1.3
y = np.arange(len(benchmarks)) * spacing
bar_h = 0.26 * spacing

plt.figure(figsize=(10, 14))

plt.barh(
    y - bar_h,
    main_means,
    height=bar_h,
    color="#D0021B",
    label="baseline",
    xerr=main_err,
    capsize=2,
)

plt.barh(
    y,
    lin_means,
    height=bar_h,
    color="#56B4E9",
    label="lin",
    xerr=lin_err,
    capsize=2,
)

plt.barh(
    y + bar_h,
    sf_means,
    height=bar_h,
    color="#fff600",
    label="sf",
    xerr=sf_err,
    capsize=2,
)

global_max = max(main_means + lin_means + sf_means)
x_offset = global_max * 0.03

# Speedup (vs. baseline) next to the lin and sf bars
for i in range(len(benchmarks)):
    plt.text(
        sf_means[i] + sf_err[i] + x_offset,
        y[i] + bar_h,
        f"{speedups_sf[i]:.2f}×",
        va="center",
        fontweight="bold",
        color="black",
    )

plt.yticks(y, benchmarks)
plt.xlabel("Mean execution time (s)")

plt.gca().invert_yaxis()
plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)
plt.legend(frameon=False, loc="lower right")

plt.grid(axis="x", linestyle="--", alpha=0.3)
plt.tick_params(axis="y", pad=6)

plt.margins(x=0.12, y=0.03)

plt.tight_layout()

plt.savefig("runtime.svg", bbox_inches="tight")
plt.show()
