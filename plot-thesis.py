from pathlib import Path
import polars as pl
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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
    label="without optimization",
    xerr=main_err,
    capsize=2
)

# lin (red)
plt.barh(
    y + bar_h/2,
    lin_means,
    height=bar_h,
    color="indianred",
    label="with optimization",
    xerr=lin_err,
    capsize=2
)

speedups = speedup_table["speedup"].to_list()

for i, s in enumerate(speedups):
    plt.text(
        max(max(main_means), max(lin_means)) * 1.05,
        y[i],
        f"{s:.2f}×",
        va="center",
        fontsize=8
    )

    plt.margins(x=0.1)

plt.yticks(y, benchmarks, fontsize=8)
plt.xlabel("Mean runtime (s)")

plt.gca().invert_yaxis()
plt.gca().spines["top"].set_visible(False)
plt.gca().spines["right"].set_visible(False)
plt.legend(frameon=False, loc="lower right")

plt.grid(axis="x", linestyle="--", alpha=0.3)
plt.tick_params(axis='y', pad=6)

plt.tight_layout()
plt.show()
