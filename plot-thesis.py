from pathlib import Path
import polars as pl
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# SVG config
mpl.rcParams.update({
    "font.size": 13,
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
                .otherwise(pl.lit("main"))
                .alias("variant")
        )
    )

    rows.append(df)

df = pl.concat(rows)
df = df.filter(~pl.col("benchmark").str.contains("Goto"))

speedup_table = (
    df
    .pivot(
        values="mean",
        index="benchmark",
        on="variant",
    )
    .with_columns(
        (pl.col("main") / pl.col("lin")).alias("speedup")
    )
    .sort("speedup", descending=True)
)

results = (
    df
    .pivot(
        values=["mean", "stddev"],
        index="benchmark",
        on="variant",
    )
    .with_columns(
        (pl.col("mean_main") / pl.col("mean_lin")).alias("speedup")
    )
    .sort("benchmark")
)

for row in results.iter_rows(named=True):
    print(
        f"`{row['benchmark']}`, "
        f"[{row['mean_main']:.5f}s], "
        f"[{row['stddev_main']:.5f}s], "
        f"[{row['mean_lin']:.5f}s], "
        f"[{row['stddev_lin']:.5f}s], "
        f"[{row['speedup']:.3f}],"
    )

geomean_speedup = (
    results
    .select(
        pl.col("speedup").log().mean().exp().alias("geomean_speedup")
    )
    .item()
)

print(f"\nGeometric mean speedup: {geomean_speedup:.3f}×")

plot_df = (
    df
    .join(
        speedup_table.select(["benchmark", "speedup"]),
        on="benchmark",
    )
)

pdf = plot_df.to_pandas()
order = speedup_table.get_column("benchmark").to_list()
pdf["benchmark"] = pd.Categorical(pdf["benchmark"], categories=order, ordered=True)

benchmarks = order

spacing = 1.3
y = np.arange(len(benchmarks)) * spacing
bar_h = 0.35 * spacing

main_means = []
lin_means = []
main_err = []
lin_err = []

for b in benchmarks:
    sub = pdf[pdf["benchmark"] == b]

    main_means.append(sub[sub["variant"] == "main"]["mean"].values[0])
    lin_means.append(sub[sub["variant"] == "lin"]["mean"].values[0])

    main_err.append(sub[sub["variant"] == "main"]["stddev"].values[0])
    lin_err.append(sub[sub["variant"] == "lin"]["stddev"].values[0])

plt.figure(figsize=(10, 12))

# main (blue)
plt.barh(
    y - bar_h/2,
    main_means,
    height=bar_h,
    color="steelblue",
    label="baseline",
    xerr=main_err,
    capsize=2
)

# lin (red)
plt.barh(
    y + bar_h/2,
    lin_means,
    height=bar_h,
    color="indianred",
    label="optimized",
    xerr=lin_err,
    capsize=2
)

speedups = speedup_table["speedup"].to_list()

global_max = max(main_means + lin_means)
x_offset = global_max * 0.03

for i, s in enumerate(speedups):
    x_pos = max(main_means[i], lin_means[i]) + x_offset

    plt.text(
        x_pos,
        y[i],
        f"{s:.2f}×",
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
plt.tick_params(axis='y', pad=6)

plt.margins(x=0.12, y=0.03)

plt.tight_layout()

plt.savefig("runtime.svg", bbox_inches="tight")
plt.show()
