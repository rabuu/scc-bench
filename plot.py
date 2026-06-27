from pathlib import Path

import polars as pl
import plotly.express as px

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
benchmark_order = speedup_table.get_column("benchmark").to_list()

summary = (
    speedup_table
    .filter(~pl.col("benchmark").str.contains("Goto"))
    .select([
        pl.len().alias("benchmarks"),
        pl.col("speedup").median().alias("median_speedup"),
        pl.col("speedup").log().mean().exp().alias("geomean_speedup"),
        pl.col("speedup").min().alias("min_speedup"),
        pl.col("speedup").max().alias("max_speedup"),
    ])
)

print(summary)

fig = px.bar(
    df.to_pandas(),
    x="benchmark",
    y="mean",
    color="variant",
    error_y="stddev",
    barmode="group",
    category_orders={
        "benchmark": benchmark_order,
        "variant": ["main", "lin"],
    },
    labels={
        "mean": "Mean runtime (s)",
        "benchmark": "Benchmark",
        "variant": "Variant",
    },
    title="Benchmark Comparison",
)

fig.update_layout(
    template="plotly_white",
    legend_title_text="",
)

fig.show()
