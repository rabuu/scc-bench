from pathlib import Path

import polars as pl
import plotly.express as px

df = pl.read_csv("file_sizes.csv")

df = df.with_columns(
    ((pl.col("main") - pl.col("lin")) / pl.col("main") * 100).alias("reduction")
).sort("reduction", descending=True)

fig = px.bar(
    df.to_pandas(),
    x="benchmark",
    y="reduction",
    title="Codesize Improvements",
    labels = {
        "reduction": "Reduction (%)",
        "benchmark": "Benchmark",
    },
)

fig.update_layout(
    template="plotly_white",
    legend_title_text="",
)

fig.show()
# fig.write_html("benchmark-codesize.html", include_plotlyjs="cdn")
