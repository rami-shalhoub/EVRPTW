from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from shiny import App, reactive, render, ui

DATA_DIR = Path(__file__).parent
df = pd.read_csv(DATA_DIR / "algo_run_data.csv")
conv_df = pd.read_csv(DATA_DIR / "convergence_data.csv") if (DATA_DIR / "convergence_data.csv").exists() else pd.DataFrame()
meta_df = pd.read_csv(DATA_DIR / "algo_run_metadata.csv") if (DATA_DIR / "algo_run_metadata.csv").exists() else pd.DataFrame()

instances = sorted(df["instance"].unique() if not df.empty else (conv_df["instance"].unique() if not conv_df.empty else []))
algorithms = sorted(df["algorithm"].unique() if not df.empty else [])
max_run = int(df["run"].max()) if not df.empty else 0

COLORS = {"greedy": "#1f77b4", "ls": "#ff7f0e", "sa": "#2ca02c", "sa_ext": "#d62728"}
ALGO_LABELS = {"greedy": "Greedy", "ls": "Local Search", "sa": "SA", "sa_ext": "SA Extended"}


def _fig_to_html(fig):
    fig.update_layout(
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Monospace", bordercolor="gray"),
    )
    return ui.markdown(
        f'<div style="overflow-x:auto;">{fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displayModeBar": True, "responsive": True})}</div>'
    )


def _fig_to_png_bytes(fig, width=1200, height=800):
    buf = BytesIO()
    fig.write_image(buf, format="png", scale=2, width=width, height=height)
    buf.seek(0)
    return buf


def best_worst_avg(s):
    return dict(best=s.min(), worst=s.max(), avg=s.mean())


def build_convergence_fig(data, metrics=("best", "worst", "avg")):
    """Route cost (best/worst/avg across runs) convergence for all algorithms,
    plus temperature schedule for SA/SA_ext."""
    if data.empty:
        return None
    if "cost" not in data.columns:
        return None

    metric_map = [("best", "min", "Best", "solid"), ("worst", "max", "Worst", "dash"),
                  ("avg", "mean", "Avg", "dot")]
    selected = [m for m in metric_map if m[0] in metrics]

    # Only algorithms that actually have convergence rows
    present = [a for a in ["greedy", "ls", "sa", "sa_ext"] if a in data["algorithm"].values]
    has_sa = any(a in present for a in ("sa", "sa_ext"))
    rows = 2 if has_sa else 1
    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        subplot_titles=(
            "Route Cost Convergence (best / worst / average across runs)",
            *(["Temperature Schedule (average across runs)"] if has_sa else []),
        ),
    )

    for algo in present:
        a_data = data[data["algorithm"] == algo]
        base = ALGO_LABELS.get(algo, algo)
        for inst in a_data["instance"].unique():
            inst_data = a_data[a_data["instance"] == inst]
            grouped = inst_data.groupby("iteration")["cost"].agg(["min", "max", "mean"]).reset_index()
            for metric, col, label, dash in selected:
                fig.add_trace(go.Scatter(
                    x=grouped["iteration"], y=grouped[col], mode="lines",
                    name=f"{base} {inst} – {label}", legendgroup=f"{algo}-{inst}",
                    line=dict(color=COLORS[algo], dash=dash, width=2),
                    hovertemplate=f"<b>{base} – {inst}</b><br>Iteration: %{{x}}<br>{label} cost: %{{y:.2f}}<extra></extra>",
                ), row=1, col=1)
            if has_sa and algo in ("sa", "sa_ext"):
                temp_grp = inst_data.groupby("iteration")["temperature"].mean().reset_index()
                fig.add_trace(go.Scatter(
                    x=temp_grp["iteration"], y=temp_grp["temperature"], mode="lines",
                    name=f"{base} {inst} – Temp", legendgroup=f"{algo}-{inst}-temp", showlegend=False,
                    line=dict(color=COLORS[algo], width=2, dash="dot"),
                    hovertemplate=f"<b>{base} – {inst}</b><br>Iteration: %{{x}}<br>Avg temperature: %{{y:.3e}}<extra></extra>",
                ), row=2, col=1)

    if has_sa:
        fig.update_xaxes(title_text="Iteration", row=2, col=1)
        fig.update_yaxes(title_text="Temperature", type="log", row=2, col=1)
    fig.update_xaxes(title_text="Iteration", row=1, col=1)
    fig.update_yaxes(title_text="Route cost", row=1, col=1)
    fig.update_layout(height=720 if has_sa else 520, template="plotly_white",
                      margin=dict(l=60, r=20, t=60, b=60), legend=dict(title="Series", orientation="h"))
    return fig


def build_route_count_fig(meta, conv=None):
    """Per-instance grouped bar chart: route count after each run per algorithm.

    Route counts per run are taken from the convergence data (which records the
    real per-run/per-mode final route count) for greedy/ls, and from the metadata
    for sa/sa_ext, since SA convergence does not track route counts.
    """
    conv = pd.DataFrame() if conv is None else conv
    if meta.empty:
        return None

    records = []
    # greedy / ls: real per-run final route count from convergence (max iteration per run)
    if not conv.empty and "routes_count" in conv.columns:
        for algo in ["greedy", "ls"]:
            sub = conv[conv["algorithm"] == algo]
            if sub.empty:
                continue
            for (inst, run_idx), grp in sub.groupby(["instance", "run"]):
                records.append({
                    "instance": inst, "algorithm": algo, "run": int(run_idx),
                    "routes_count": grp["routes_count"].max(),
                })
    # sa / sa_ext: use metadata routes_count per run
    for algo in ["sa", "sa_ext"]:
        sub = meta[meta["algorithm"] == algo]
        if sub.empty:
            continue
        for _, row in sub.iterrows():
            records.append({
                "instance": row["instance"], "algorithm": algo, "run": int(row["run"]),
                "routes_count": row["routes_count"],
            })

    if not records:
        return None
    rc = pd.DataFrame(records)
    if rc.empty:
        return None

    inst_list = sorted(rc["instance"].unique())
    ncols = 2
    nrows = (len(inst_list) + ncols - 1) // ncols
    fig = make_subplots(rows=nrows, cols=ncols,
                        subplot_titles=[f"{i}" for i in inst_list],
                        vertical_spacing=0.10, horizontal_spacing=0.08)

    for idx, inst in enumerate(inst_list):
        r, c = idx // ncols + 1, idx % ncols + 1
        for algo in ["greedy", "ls", "sa", "sa_ext"]:
            a_df = rc[(rc["algorithm"] == algo) & (rc["instance"] == inst)]
            if a_df.empty:
                continue
            a_df = a_df.sort_values("run")
            fig.add_trace(go.Bar(
                x=[f"Run {r_}" for r_ in a_df["run"]], y=a_df["routes_count"],
                name=ALGO_LABELS.get(algo, algo),
                legendgroup=algo,
                showlegend=(idx == 0),
                offsetgroup=algo,
                marker_color=COLORS[algo],
                hovertemplate=f"<b>{ALGO_LABELS.get(algo, algo)} – {inst}</b><br>Run: %{{x}}<br>Routes: %{{y}}<extra></extra>",
            ), row=r, col=c)
        fig.update_xaxes(title_text="Run", row=r, col=c, tickangle=0)
        fig.update_yaxes(title_text="Routes", row=r, col=c, dtick=1)

    fig.update_layout(height=320 * nrows, barmode="group", template="plotly_white",
                      margin=dict(l=60, r=20, t=60, b=40), legend=dict(title="Algorithm"))
    return fig


def build_pipeline_fig(data):
    if data.empty:
        return None
    algo_order = ["greedy", "ls", "sa", "sa_ext"]
    fig = go.Figure()
    for inst in data["instance"].unique():
        inst_data = data[data["instance"] == inst]
        best_costs, present_algos = [], []
        for algo in algo_order:
            a_df = inst_data[inst_data["algorithm"] == algo]
            if not a_df.empty:
                best_costs.append(a_df["cost"].min())
                present_algos.append(algo)
        if len(present_algos) >= 2:
            fig.add_trace(go.Scatter(
                x=[ALGO_LABELS[a] for a in present_algos], y=best_costs,
                mode="lines+markers+text", name=inst,
                text=[f"{c:.1f}" for c in best_costs], textposition="top center",
                line=dict(width=2), marker=dict(size=10),
                hovertemplate=f"<b>{inst}</b><br>Algorithm: %{{x}}<br>Best cost: %{{y:.2f}}<extra></extra>",
            ))
    fig.update_xaxes(title_text="Algorithm stage")
    fig.update_yaxes(title_text="Best cost")
    fig.update_layout(height=600, template="plotly_white",
                      margin=dict(l=60, r=20, t=50, b=60), legend=dict(title="Instance"))
    return fig


def build_internals_fig(meta):
    """SA/SA_ext acceptance rate (% per run) + LS improvements/ejected."""
    if meta.empty:
        return None
    sa_data = meta[meta["algorithm"].isin(["sa", "sa_ext"])]
    ls_data = meta[meta["algorithm"] == "ls"]
    has_sa = not sa_data.empty
    has_ls = not ls_data.empty

    if has_sa and has_ls:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.14,
                            subplot_titles=("SA / SA_ext: Move Counts per Run (accepted / rejected / infeasible / improving)",
                                            "Local Search: Improvements & Ejected per Run"))
    elif has_sa:
        fig = make_subplots(rows=1, cols=1,
                            subplot_titles=("SA / SA_ext: Move Counts per Run (accepted / rejected / infeasible / improving)"))
    elif has_ls:
        fig = make_subplots(rows=1, cols=1,
                            subplot_titles=("Local Search: Improvements & Ejected per Run"))
    else:
        return None

    row = 1
    if has_sa:
        sa_metrics = [
            ("accepted_moves", "Accepted", "#2ca02c"),
            ("rejected_moves", "Rejected", "#d62728"),
            ("infeasible_moves", "Infeasible", "#ff7f0e"),
            ("improving_moves", "Improving", "#9467bd"),
        ]
        for algo in ["sa", "sa_ext"]:
            if algo not in sa_data["algorithm"].values:
                continue
            a_df = sa_data[sa_data["algorithm"] == algo]
            runs_sorted = sorted(a_df["run"].unique())
            for col, label, color in sa_metrics:
                per_run = [a_df[a_df["run"] == r][col].sum() for r in runs_sorted]
                fig.add_trace(go.Bar(
                    x=[f"Run {r}" for r in runs_sorted], y=per_run,
                    name=f"{ALGO_LABELS.get(algo, algo)} – {label}",
                    marker_color=color, legendgroup=algo, showlegend=True,
                    hovertemplate=f"<b>{ALGO_LABELS.get(algo, algo)} – {label}</b><br>Run: %{{x}}<br>Count: %{{y}}<extra></extra>",
                ), row=row, col=1)
        fig.update_yaxes(title_text="Move count", row=row, col=1)
        if has_ls:
            row += 1

    if has_ls:
        runs_sorted = sorted(ls_data["run"].unique())
        for r in runs_sorted:
            sub = ls_data[ls_data["run"] == r]
            fig.add_trace(go.Bar(
                x=[f"Run {r}"], y=[sub["improvements_made"].mean()],
                name=f"Improvements run {r}", marker_color=COLORS["ls"], offsetgroup="imp",
                hovertemplate=f"<b>Local Search</b><br>Run: {r}<br>Improvements: %{{y}}<extra></extra>",
            ), row=row, col=1)
            fig.add_trace(go.Bar(
                x=[f"Run {r}"], y=[sub["ejected_customers"].mean()],
                name=f"Ejected run {r}", marker_color="#9467bd", offsetgroup="ej",
                hovertemplate=f"<b>Local Search</b><br>Run: {r}<br>Customers moved to solo routes (D,C,D): %{{y}}<extra></extra>",
            ), row=row, col=1)
        fig.update_yaxes(title_text="Count", row=row, col=1)
        fig.update_xaxes(title_text="Run", row=row, col=1)

    fig.update_layout(height=700 if has_sa and has_ls else 500, barmode="group",
                      template="plotly_white", margin=dict(l=60, r=20, t=60, b=60))
    return fig


# ── UI ───────────────────────────────────────────────────────────────────
app_ui = ui.page_navbar(
    ui.nav_panel(
        "Convergence",
        ui.card(
            ui.card_header("Route Cost Convergence & Temperature"),
            ui.tags.div(
                ui.input_checkbox_group("conv_metrics", "Metrics to show",
                                        choices={"best": "Best", "worst": "Worst", "avg": "Average"},
                                        selected=["best", "worst", "avg"]),
                style="margin-top:0.5rem;",
            ),
            ui.output_ui("convergence_plot"),
            ui.download_button("dl_convergence", "Download PNG", class_="btn-sm"),
            full_screen=True,
        ),
    ),
    ui.nav_panel(
        "Route Count",
        ui.card(
            ui.card_header("Route Count After Each Run (per Algorithm)"),
            ui.output_ui("route_count_plot"),
            ui.download_button("dl_route_count", "Download PNG", class_="btn-sm"),
            full_screen=True,
        ),
    ),
    ui.nav_panel(
        "Algorithm Pipeline",
        ui.card(
            ui.card_header("Algorithm Pipeline (Greedy -> LS -> SA -> SA_ext)"),
            ui.output_ui("pipeline_plot"),
            ui.download_button("dl_pipeline", "Download PNG", class_="btn-sm"),
            full_screen=True,
        ),
    ),
    ui.nav_panel(
        "Algorithm Internals",
        ui.card(
            ui.card_header("Algorithm Internals"),
            ui.output_ui("internals_plot"),
            ui.download_button("dl_internals", "Download PNG", class_="btn-sm"),
            full_screen=True,
        ),
    ),
    sidebar=ui.sidebar(
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
            ui.input_checkbox_group("algo", "Algorithm", choices=algorithms, selected=algorithms),
            class_="grid-2",
        ),
        ui.tags.div(
            ui.input_checkbox_group("inst", "Instances", choices=instances, selected=instances),
            class_="grid-2",
        ),
        ui.tags.div(
            ui.input_checkbox_group(
                "runs", "Runs",
                choices={str(i): str(i) for i in range(max_run + 1)},
                selected=[str(i) for i in range(max_run + 1)],
            ),
            class_="grid-2",
        ),
        ui.input_dark_mode(),
        width=300,
    ),
    title="EVRPTW Algorithm Dashboard",
)


# ── Server ───────────────────────────────────────────────────────────────
def server(input, output, session):

    @reactive.calc
    def filtered():
        sub = df[df["instance"].isin(input.inst())]
        sub = sub[sub["algorithm"].isin(input.algo())]
        sub = sub[sub["run"].astype(str).isin(input.runs())]
        return sub

    @reactive.calc
    def filtered_meta():
        if meta_df.empty:
            return meta_df
        sub = meta_df[meta_df["instance"].isin(input.inst())]
        sub = sub[sub["algorithm"].isin(input.algo())]
        sub = sub[sub["run"].astype(str).isin(input.runs())]
        return sub

    @reactive.calc
    def filtered_conv():
        if conv_df.empty:
            return conv_df
        sub = conv_df[conv_df["instance"].isin(input.inst())]
        sub = sub[sub["algorithm"].isin(input.algo())]
        sub = sub[sub["run"].astype(str).isin(input.runs())]
        return sub

    # ── Tab 1: Convergence ──────────────────────────────────────────
    @render.ui
    def convergence_plot():
        if conv_df.empty:
            return ui.p("Run the solver to generate convergence_data.csv")
        fig = build_convergence_fig(filtered_conv(), input.conv_metrics())
        if fig is None:
            return ui.p("No convergence data (SA/SA_ext) for the selected filters.")
        return _fig_to_html(fig)

    @render.download(filename="convergence.png")
    def dl_convergence():
        if conv_df.empty:
            return
        fig = build_convergence_fig(filtered_conv(), input.conv_metrics())
        if fig is None:
            return
        yield _fig_to_png_bytes(fig)

    # ── Tab 2: Route Count ──────────────────────────────────────────
    @render.ui
    def route_count_plot():
        if meta_df.empty:
            return ui.p("Run the solver to generate algo_run_metadata.csv")
        fig = build_route_count_fig(filtered_meta(), filtered_conv())
        if fig is None:
            return ui.p("No metadata for the selected filters.")
        return _fig_to_html(fig)

    @render.download(filename="route_count.png")
    def dl_route_count():
        if meta_df.empty:
            return
        fig = build_route_count_fig(filtered_meta(), filtered_conv())
        if fig is None:
            return
        yield _fig_to_png_bytes(fig)

    # ── Tab 3: Algorithm Pipeline ───────────────────────────────────
    @render.ui
    def pipeline_plot():
        if meta_df.empty:
            return ui.p("Run the solver to generate algo_run_metadata.csv")
        fig = build_pipeline_fig(filtered_meta())
        if fig is None:
            return ui.p("No metadata for the selected filters.")
        return _fig_to_html(fig)

    @render.download(filename="algorithm_pipeline.png")
    def dl_pipeline():
        if meta_df.empty:
            return
        fig = build_pipeline_fig(filtered_meta())
        if fig is None:
            return
        yield _fig_to_png_bytes(fig)

    # ── Tab 4: Algorithm Internals ──────────────────────────────────
    @render.ui
    def internals_plot():
        if meta_df.empty:
            return ui.p("Run the solver to generate algo_run_metadata.csv")
        fig = build_internals_fig(filtered_meta())
        if fig is None:
            return ui.p("No metadata for the selected filters.")
        return _fig_to_html(fig)

    @render.download(filename="algorithm_internals.png")
    def dl_internals():
        if meta_df.empty:
            return
        fig = build_internals_fig(filtered_meta())
        if fig is None:
            return
        yield _fig_to_png_bytes(fig)


app = App(app_ui, server)
