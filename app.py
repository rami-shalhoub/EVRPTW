from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import App, reactive, render, ui

CSV_PATH = Path(__file__).parent / "algo_run_data.csv"
df = pd.read_csv(CSV_PATH)
instances = sorted(df["instance"].unique())
algorithms = sorted(df["algorithm"].unique())
max_run = int(df["run"].max())

COLORS = {"greedy": "#1f77b4", "ls": "#ff7f0e"}
STAT_LABELS = {"min": "Best", "mean": "Avg", "max": "Worst"}

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Plot",
        ui.page_sidebar(
            ui.sidebar(
                ui.tags.style("""
                  .sidebar .control-label { margin-bottom: 0.25rem !important; }
                  .grid-2 .shiny-options-group {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 0 0.5rem;
                  }
                  .grid-2 .checkbox { margin-top: 0; margin-bottom: 0; }
                """),
                ui.h5("Filters"),
                ui.tags.div(
                    ui.input_checkbox_group(
                        "algo",
                        "Algorithm",
                        choices=algorithms,
                        selected=algorithms,
                    ),
                    class_="grid-2",
                ),
                ui.tags.div(
                    ui.input_checkbox_group(
                        "inst",
                        "Instances",
                        choices=instances,
                        selected=instances,
                    ),
                    class_="grid-2",
                ),
                ui.tags.div(
                    ui.input_checkbox_group(
                        "runs",
                        "Runs",
                        choices={str(i): str(i) for i in range(max_run + 1)},
                        selected=[str(i) for i in range(max_run + 1)],
                    ),
                    class_="grid-2",
                ),
                ui.hr(),
                ui.h5("Plot options"),
                ui.input_select(
                    "plot_type",
                    "Plot type",
                    choices={
                        "bar": "Bar",
                        "box": "Box",
                        "line": "Line",
                    },
                    selected="bar",
                ),
                ui.tags.div(
                    ui.input_checkbox_group(
                        "stats",
                        "Aggregation (bar only)",
                        choices={"min": "Best", "mean": "Avg", "max": "Worst"},
                        selected=["min"],
                    ),
                    style="margin-top: 0.5rem;",
                ),
                ui.input_dark_mode(),
                width=300,
            ),
            ui.card(
                ui.card_header("Cost & Time"),
                ui.output_ui("plot"),
                full_screen=True,
            ),
            fillable=True,
        ),
    ),
    ui.nav_panel(
        "Table",
        ui.card(
            ui.card_header("Run data"),
            ui.output_data_frame("table"),
            full_screen=True,
        ),
    ),
    title="EVRPTW Algorithm Dashboard",
)


def server(input, output, session):
    @reactive.calc
    def filtered():
        sub = df[df["instance"].isin(input.inst())]
        sub = sub[sub["algorithm"].isin(input.algo())]
        sub = sub[sub["run"].astype(str).isin(input.runs())]
        return sub

    @render.data_frame
    def table():
        return render.DataGrid(
            filtered().round(4),
            filters=True,
        )

    @render.ui
    def plot():
        data = filtered()
        if data.empty:
            return ui.p("No data for the selected filters.")

        match input.plot_type():
            # ── Bar ────────────────────────────────────────────
            case "bar":
                selected_stats = input.stats()
                if selected_stats:
                    stats_map = {
                        "min": "min",
                        "mean": "mean",
                        "max": "max",
                    }
                    aggs = data.groupby(["instance", "algorithm"])[["cost", "time"]].agg(
                        list(stats_map.values())
                    ).reset_index()
                    aggs.columns = [
                        "_".join(c for c in col if c).rstrip("_")
                        for col in aggs.columns
                    ]

                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.12,
                        subplot_titles=("Cost", "Time (s)"),
                    )

                    instances_plot = data["instance"].unique()
                    seen = set()
                    for algo in algorithms:
                        if algo not in data["algorithm"].values:
                            continue
                        algo_aggs = aggs[aggs["algorithm"] == algo]
                        show_legend = algo not in seen
                        seen.add(algo)

                        x_labels = []
                        cost_bars = {}
                        time_bars = {}
                        for stat in selected_stats:
                            cost_col = f"cost_{stat}"
                            time_col = f"time_{stat}"
                            cost_bars[stat] = []
                            time_bars[stat] = []
                            for inst_val in instances_plot:
                                row = algo_aggs[algo_aggs["instance"] == inst_val]
                                if not row.empty:
                                    if len(x_labels) < len(instances_plot) * len(selected_stats):
                                        x_labels.append(f"{inst_val}")
                                    cost_bars[stat].append(row[cost_col].values[0])
                                    time_bars[stat].append(row[time_col].values[0])
                                else:
                                    if len(x_labels) < len(instances_plot) * len(selected_stats):
                                        x_labels.append(f"{inst_val}")
                                    cost_bars[stat].append(0)
                                    time_bars[stat].append(0)

                        x_labels = list(instances_plot)
                        n = len(x_labels)
                        w = 0.25
                        offsets = {
                            s: (i - (len(selected_stats) - 1) / 2) * w
                            for i, s in enumerate(selected_stats)
                        }

                        for stat in selected_stats:
                            fig.add_trace(
                                go.Bar(
                                    name=STAT_LABELS[stat],
                                    x=x_labels,
                                    y=cost_bars[stat],
                                    legendgroup=algo,
                                    showlegend=(algo == algorithms[0]),
                                    marker_color=COLORS[algo],
                                    offsetgroup=stat,
                                    hovertemplate=f"{algo}<br>{STAT_LABELS[stat]}: %{{y:.2f}}<extra></extra>",
                                ),
                                row=1,
                                col=1,
                            )
                            fig.add_trace(
                                go.Bar(
                                    name=STAT_LABELS[stat],
                                    x=x_labels,
                                    y=time_bars[stat],
                                    legendgroup=algo,
                                    showlegend=False,
                                    marker_color=COLORS[algo],
                                    offsetgroup=stat,
                                    hovertemplate=f"{algo}<br>{STAT_LABELS[stat]}: %{{y:.4f}}s<extra></extra>",
                                ),
                                row=2,
                                col=1,
                            )

                    fig.update_xaxes(tickangle=45)
                    fig.update_yaxes(title_text="Cost", row=1, col=1)
                    fig.update_yaxes(title_text="Time (s)", row=2, col=1)
                    fig.update_layout(
                        height=700,
                        barmode="group",
                        template="plotly_white",
                        margin=dict(l=40, r=20, t=50, b=80),
                    )
                else:
                    fig = make_subplots(
                        rows=2,
                        cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.12,
                        subplot_titles=("Cost per Run", "Time (s) per Run"),
                    )

                    seen = set()
                    for algo in algorithms:
                        if algo not in data["algorithm"].values:
                            continue
                        algo_df = data[data["algorithm"] == algo]
                        show_legend = algo not in seen
                        seen.add(algo)

                        for inst in algo_df["instance"].unique():
                            inst_df = algo_df[algo_df["instance"] == inst]
                            labels = [f"{inst}<br>run {r}" for r in inst_df["run"]]

                            fig.add_trace(
                                go.Bar(
                                    name=algo,
                                    x=labels,
                                    y=inst_df["cost"],
                                    legendgroup=algo,
                                    showlegend=show_legend,
                                    marker_color=COLORS[algo],
                                    hovertemplate=f"{algo}<br>Cost=%{{y:.2f}}<extra></extra>",
                                ),
                                row=1,
                                col=1,
                            )
                            fig.add_trace(
                                go.Bar(
                                    name=algo,
                                    x=labels,
                                    y=inst_df["time"],
                                    legendgroup=algo,
                                    showlegend=False,
                                    marker_color=COLORS[algo],
                                    hovertemplate=f"{algo}<br>Time=%{{y:.4f}}s<extra></extra>",
                                ),
                                row=2,
                                col=1,
                            )
                            show_legend = False

                    fig.update_xaxes(tickangle=45)
                    fig.update_yaxes(title_text="Cost", row=1, col=1)
                    fig.update_yaxes(title_text="Time (s)", row=2, col=1)
                    fig.update_layout(
                        height=700,
                        barmode="group",
                        template="plotly_white",
                        margin=dict(l=40, r=20, t=50, b=80),
                    )

            # ── Box ────────────────────────────────────────────
            case "box":
                fig = make_subplots(
                    rows=1,
                    cols=2,
                    subplot_titles=("Cost", "Time (s)"),
                    horizontal_spacing=0.12,
                )

                for i, (metric, title) in enumerate(
                    [("cost", "Cost"), ("time", "Time (s)")], start=1
                ):
                    for algo in data["algorithm"].unique():
                        algo_df = data[data["algorithm"] == algo]
                        fig.add_trace(
                            go.Box(
                                y=algo_df[metric],
                                x=algo_df["instance"],
                                name=algo,
                                legendgroup=algo,
                                showlegend=(i == 1),
                                marker_color=COLORS[algo],
                                boxmean="sd",
                            ),
                            row=1,
                            col=i,
                        )
                    fig.update_xaxes(title_text="Instance", row=1, col=i)
                    fig.update_yaxes(title_text=title, row=1, col=i)

                fig.update_layout(
                    height=500,
                    boxmode="group",
                    template="plotly_white",
                    margin=dict(l=40, r=20, t=50, b=80),
                )

            # ── Line ───────────────────────────────────────────
            case "line":
                fig = make_subplots(
                    rows=2,
                    cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.12,
                    subplot_titles=("Cost per Run", "Time (s) per Run"),
                )

                for algo in data["algorithm"].unique():
                    algo_df = data[data["algorithm"] == algo]
                    for inst in algo_df["instance"].unique():
                        inst_df = algo_df[algo_df["instance"] == inst].sort_values("run")

                        fig.add_trace(
                            go.Scatter(
                                x=inst_df["run"],
                                y=inst_df["cost"],
                                mode="lines+markers",
                                name=f"{algo} – {inst}",
                                legendgroup=algo,
                                showlegend=False,
                                line=dict(
                                    color=COLORS[algo],
                                    dash="solid" if algo == "greedy" else "dash",
                                ),
                                marker=dict(
                                    color=COLORS[algo],
                                    symbol="circle" if algo == "greedy" else "x",
                                ),
                                hovertemplate=f"{algo}<br>{inst}<br>Cost=%{{y:.2f}}<extra></extra>",
                            ),
                            row=1,
                            col=1,
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=inst_df["run"],
                                y=inst_df["time"],
                                mode="lines+markers",
                                name=f"{algo} – {inst}",
                                legendgroup=algo,
                                showlegend=False,
                                line=dict(
                                    color=COLORS[algo],
                                    dash="solid" if algo == "greedy" else "dash",
                                ),
                                marker=dict(
                                    color=COLORS[algo],
                                    symbol="circle" if algo == "greedy" else "x",
                                ),
                                hovertemplate=f"{algo}<br>{inst}<br>Time=%{{y:.4f}}s<extra></extra>",
                            ),
                            row=2,
                            col=1,
                        )

                fig.update_xaxes(title_text="Inner run", row=2, col=1)
                fig.update_yaxes(title_text="Cost", row=1, col=1)
                fig.update_yaxes(title_text="Time (s)", row=2, col=1)
                fig.update_layout(
                    height=700,
                    template="plotly_white",
                    margin=dict(l=40, r=20, t=50, b=80),
                    hovermode="x unified",
                )

        return ui.markdown(
            f'<div style="overflow-x:auto;">{fig.to_html(include_plotlyjs="cdn", full_html=False)}</div>'
        )


app = App(app_ui, server)
