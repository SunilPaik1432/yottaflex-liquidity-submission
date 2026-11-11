import os
from contextlib import closing

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from src.scenarios import daily_scenario
from src.settlements import compare_settlements


ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("YOTTAFLEX_DB_PATH", ROOT / "database" / "liquidity.db"))
FORECAST_CUTOFF = "2026-11-10"

st.set_page_config(page_title="YottaFlex Liquidity Dashboard", layout="wide")

pio.templates["yottaflex"] = pio.templates["plotly_white"]
pio.templates["yottaflex"].layout.colorway = [
    "#7868E8", "#F17B91", "#32B8A3", "#F0B44C", "#6289ED"
]
pio.templates.default = "yottaflex"

st.markdown("""
<style>
:root {
    --ink:#302653;
    --muted:#716D87;
    --violet:#7868E8;
    --rose:#F17B91;
    --mint:#32B8A3;
    --line:#E6E2F2;
}
.stApp {
    background:
        radial-gradient(ellipse at 8% 0%,#F0ECFF 0%,transparent 34%),
        radial-gradient(ellipse at 94% 6%,#FFF0F3 0%,transparent 28%),
        #F8F8FC;
    color:var(--ink);
}
.block-container {
    max-width:1480px;
    padding-top:1.2rem;
    padding-bottom:3rem;
}
[data-testid="stHeader"] {
    background:transparent;
}
.hero {
    position:relative;
    overflow:hidden;
    transform-style:preserve-3d;
    background:linear-gradient(118deg,#FFF3F1 0%,#F0EDFF 55%,#EAF7FF 100%);
    border:1px solid #E4DFF3;
    border-bottom:3px solid #9184EF;
    border-radius:24px;
    padding:31px 36px;
    margin:0 0 20px 0;
    box-shadow:0 14px 34px rgba(75,60,135,.10);
    transition:transform .35s ease,box-shadow .35s ease;
}
.hero:hover {
    transform:perspective(1100px) rotateX(1deg) translateY(-3px);
    box-shadow:0 20px 42px rgba(75,60,135,.16);
}
.hero:after {
    content:"";
    position:absolute;
    width:176px;
    height:176px;
    right:8%;
    top:-48px;
    border-radius:50%;
    background:radial-gradient(circle at 30% 25%,#FFF 0%,#D6CEFF 30%,#9A8AF3 65%,#7160D8 100%);
    box-shadow:inset -14px -18px 28px rgba(66,48,157,.18),0 18px 38px rgba(107,89,213,.22);
    transform:translateZ(42px);
    opacity:.86;
    pointer-events:none;
    animation:orb-float 7s ease-in-out infinite;
}
@keyframes orb-float {
    0%,100% { transform:translate3d(0,0,42px); }
    50% { transform:translate3d(0,-8px,54px); }
}
.hero-kicker {
    color:#7364CF;
    font-size:.72rem;
    font-weight:800;
    letter-spacing:.17em;
    margin:0 0 9px 0;
}
.hero-title {
    color:#302653;
    font-size:2.15rem;
    line-height:1.16;
    font-weight:800;
    margin:0;
    text-shadow:0 1px 0 #FFF;
}
.hero-subtitle {
    color:#6F6B86;
    font-size:.98rem;
    margin:9px 0 0 0;
    max-width:620px;
}
.section-kicker {
    color:#8779D8;
    font-size:.72rem;
    font-weight:800;
    letter-spacing:.14em;
    margin:10px 0 10px 2px;
}
[data-testid="stMetric"] {
    background:linear-gradient(155deg,#FFF 0%,#FBFAFF 100%);
    border:1px solid #E8E4F2;
    border-radius:18px;
    padding:17px 18px;
    box-shadow:0 6px 17px rgba(48,38,83,.055);
    transform-style:preserve-3d;
    transition:transform .25s ease,box-shadow .25s ease;
}
[data-testid="stMetric"]:hover {
    transform:perspective(900px) translateY(-4px) rotateX(2deg);
    box-shadow:0 14px 27px rgba(48,38,83,.12);
}
[data-testid="stMetricLabel"] {
    color:var(--muted);
    font-weight:650;
}
[data-testid="stMetricValue"] {
    color:var(--ink);
    font-weight:780;
}
[data-testid="stPlotlyChart"] {
    background:rgba(255,255,255,.92);
    border:1px solid var(--line);
    border-radius:18px;
    padding:8px;
    box-shadow:0 7px 20px rgba(48,38,83,.055);
    transition:transform .25s ease,box-shadow .25s ease;
}
[data-testid="stPlotlyChart"]:hover {
    transform:translateY(-2px);
    box-shadow:0 13px 28px rgba(48,38,83,.10);
}
[data-testid="stDataFrame"] {
    border:1px solid var(--line);
    border-radius:14px;
    overflow:hidden;
    box-shadow:0 5px 16px rgba(48,38,83,.04);
}
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#F2F0FB 0%,#FAF9FD 100%);
    border-right:1px solid #E4E0EF;
}
[data-testid="stSidebar"] [data-testid="stButton"] button {
    background:linear-gradient(110deg,#7868E8,#A06DD3);
    color:#FFF;
    border:0;
    border-radius:11px;
    font-weight:700;
    box-shadow:0 6px 14px rgba(120,104,232,.22);
}
[data-testid="stSidebar"] [data-testid="stButton"] button:hover {
    background:linear-gradient(110deg,#6857D7,#8E5EC3);
    color:#FFF;
}
[data-baseweb="tab-list"] {
    gap:.38rem;
    background:#EFEDF7;
    padding:.42rem;
    border:1px solid #E4E0EF;
    border-radius:16px;
}
[data-baseweb="tab"] {
    height:2.7rem;
    background:transparent;
    border-radius:12px;
    padding:0 1.2rem;
    color:#69647E;
    font-weight:650;
}
[data-baseweb="tab"][aria-selected="true"] {
    background:#FFF;
    color:#6253C6;
    box-shadow:0 3px 10px rgba(48,38,83,.10);
}
h2,h3 {
    color:var(--ink);
    letter-spacing:-.025em;
}
@media (prefers-reduced-motion:reduce) {
    *,*::before,*::after {
        animation:none !important;
        transition:none !important;
    }
}
</style>

<div class="hero">
  <p class="hero-kicker">TREASURY ANALYTICS · DEMO</p>
  <h1 class="hero-title">YottaFlex Liquidity &amp; Risk</h1>
  <p class="hero-subtitle">Cash forecasts, projected balances and risk indicators at a glance</p>
</div>
""", unsafe_allow_html=True)

st.caption("Synthetic demo data • Amounts remain in their original currencies")


def save_scenario_runs(scenario_settings, scenario_daily):
    created = datetime.now()
    stamp = created.strftime("%Y%m%d%H%M%S%f")

    connection = sqlite3.connect(DB_PATH)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        with connection:
            cursor = connection.cursor()
            saved_rows = 0

            for scenario_name, inflow_factor, outflow_factor, receipt_delay_days in scenario_settings:
                slug = scenario_name.upper().replace(" ", "-")
                scenario_id = f"SCN-{slug}-{stamp}"
                run_id = f"RUN-{slug}-{stamp}"

                assumptions = (
                    f"Saved what-if run: inflows {inflow_factor:.2f}x, "
                    f"outflows {outflow_factor:.2f}x; receipts delayed "
                    f"{receipt_delay_days} days; synthetic INR conversion at cutoff."
                )

                cursor.execute("""
                    INSERT INTO liquidity_scenarios
                    (scenario_id, scenario_name, assumptions, created_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    scenario_id,
                    scenario_name,
                    assumptions,
                    created.isoformat(timespec="seconds")
                ))

                cursor.execute("""
                    INSERT INTO forecast_runs
                    (run_id, scenario_id, run_date, cutoff_date, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    run_id,
                    scenario_id,
                    created.date().isoformat(),
                    FORECAST_CUTOFF,
                    "COMPLETED"
                ))

                rows = scenario_daily[
                    scenario_daily["scenario"] == scenario_name
                ]

                records = [
                    (
                        f"{run_id}-{row.forecast_date}",
                        run_id,
                        row.forecast_date,
                        "INR",
                        float(row.inflow_inr),
                        float(row.outflow_inr),
                        float(row.net_flow_inr)
                    )
                    for row in rows.itertuples(index=False)
                ]

                cursor.executemany("""
                    INSERT INTO scenario_forecasts
                    (forecast_id, run_id, forecast_date, currency,
                     inflow, outflow, net_flow)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, records)

                saved_rows += len(records)

        return saved_rows

    finally:
        connection.close()


@st.cache_data(ttl=60)
def load_data(db_path):
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    with closing(sqlite3.connect(db_path)) as connection:

        counts = {
            table: pd.read_sql_query(
                f"SELECT COUNT(*) AS count FROM {table}",
                connection
            ).iloc[0, 0]
            for table in (
                "legal_entities",
                "bank_accounts",
                "ledger_entries",
                "receivables",
                "payables",
                "cash_flow_forecasts"
            )
        }

        forecast = pd.read_sql_query("""
            SELECT forecast_date, currency,
                   SUM(CASE WHEN forecast_type = 'INFLOW'
                       THEN amount ELSE 0 END) AS inflow,
                   SUM(CASE WHEN forecast_type = 'OUTFLOW'
                       THEN amount ELSE 0 END) AS outflow
            FROM cash_flow_forecasts
            GROUP BY forecast_date, currency
            ORDER BY forecast_date, currency
        """, connection)

        overdue = pd.read_sql_query("""
            SELECT 'Receivables' AS item_type, currency,
                   COUNT(*) AS item_count, SUM(amount) AS amount
            FROM receivables
            WHERE status = 'OVERDUE'
            GROUP BY currency

            UNION ALL

            SELECT 'Payables' AS item_type, currency,
                   COUNT(*) AS item_count, SUM(amount) AS amount
            FROM payables
            WHERE status = 'OVERDUE'
            GROUP BY currency
        """, connection)

        cash_position = pd.read_sql_query("""
            SELECT ba.currency,
                   SUM(
                       ba.opening_balance +
                       COALESCE(movement.net_movement, 0)
                   ) AS opening_cash
            FROM bank_accounts ba

            LEFT JOIN (
                SELECT account_id,
                       SUM(
                           CASE
                               WHEN entry_type = 'CREDIT' THEN amount
                               WHEN entry_type = 'DEBIT' THEN -amount
                               ELSE 0
                           END
                       ) AS net_movement
                FROM ledger_entries
                WHERE transaction_date < ?
                GROUP BY account_id
            ) movement
            ON movement.account_id = ba.account_id

            GROUP BY ba.currency
            ORDER BY ba.currency
        """, connection, params=(FORECAST_CUTOFF,))

        ledger_history = pd.read_sql_query("""
            SELECT l.transaction_date, a.currency,
                   SUM(
                       CASE
                           WHEN l.entry_type = 'CREDIT' THEN l.amount
                           WHEN l.entry_type = 'DEBIT' THEN -l.amount
                           ELSE 0
                       END
                   ) AS net_flow
            FROM ledger_entries l
            JOIN bank_accounts a
                ON a.account_id = l.account_id
            WHERE l.transaction_date >= date(?, '-90 days')
              AND l.transaction_date < ?
            GROUP BY l.transaction_date, a.currency
            ORDER BY l.transaction_date, a.currency
        """, connection, params=(FORECAST_CUTOFF, FORECAST_CUTOFF))

        fx_rates = pd.read_sql_query("""
            SELECT from_currency, exchange_rate
            FROM (
                SELECT from_currency, exchange_rate,
                       ROW_NUMBER() OVER (
                           PARTITION BY from_currency ORDER BY effective_date DESC, rate_id
                       ) AS rate_rank
                FROM currency_rates
                WHERE to_currency = 'INR' AND effective_date <= ?
            )
            WHERE rate_rank = 1
        """, connection, params=(FORECAST_CUTOFF,))

    return counts, forecast, overdue, fx_rates, cash_position, ledger_history


try:
    counts, forecast, overdue, fx_rates, cash_position, ledger_history = load_data(DB_PATH)

except Exception as error:
    st.error(f"Could not load project data: {error}")
    st.stop()


if forecast.empty:
    st.warning("No cash flow forecasts found. Generate a database using the README instructions.")
    st.stop()


st.sidebar.markdown("### Live controls")

if st.sidebar.button("Refresh dashboard data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()


horizon = st.sidebar.selectbox(
    "Forecast horizon",
    ["Next 14 days", "Next 30 days", "Full forecast"],
    index=2
)

if horizon != "Full forecast":
    day_count = 14 if horizon == "Next 14 days" else 30
    first_date = pd.to_datetime(forecast["forecast_date"]).min()
    last_visible_date = (
        first_date + pd.Timedelta(days=day_count - 1)
    ).strftime("%Y-%m-%d")

    forecast = forecast[
        forecast["forecast_date"] <= last_visible_date
    ].copy()


st.sidebar.caption(
    "Changing the horizon updates the forecast and projected-balance visuals."
)

st.sidebar.markdown("### What-if assumptions")

upside_inflow_pct = st.sidebar.slider(
    "Upside: inflow increase (%)", 0, 50, 10
)
upside_outflow_pct = st.sidebar.slider(
    "Upside: outflow reduction (%)", 0, 50, 5
)
downside_inflow_pct = st.sidebar.slider(
    "Downside: inflow reduction (%)", 0, 80, 20
)
downside_outflow_pct = st.sidebar.slider(
    "Downside: outflow increase (%)", 0, 100, 15
)


forecast["net_flow"] = forecast["inflow"] - forecast["outflow"]

fx_to_inr = {
    "INR": 1.0,
    **dict(zip(fx_rates["from_currency"], fx_rates["exchange_rate"]))
}

missing_fx = sorted(
    forecast.loc[forecast["currency"].map(fx_to_inr).isna(), "currency"].unique()
)

if missing_fx:
    st.error(
        f"Missing INR conversion rates for: {', '.join(missing_fx)}"
    )
    st.stop()


forecast["fx_to_inr"] = forecast["currency"].map(fx_to_inr)
forecast["inflow_inr"] = forecast["inflow"] * forecast["fx_to_inr"]
forecast["outflow_inr"] = forecast["outflow"] * forecast["fx_to_inr"]
forecast["net_flow_inr"] = (
    forecast["inflow_inr"] - forecast["outflow_inr"]
)


# Transparent weekday-average baseline from the 90 calendar days before cutoff.
history_currencies = sorted(cash_position["currency"].unique())

history_dates = pd.date_range(
    end=pd.Timestamp(FORECAST_CUTOFF) - pd.Timedelta(days=1),
    periods=90,
    freq="D"
).strftime("%Y-%m-%d")

history_grid = pd.MultiIndex.from_product(
    [history_dates, history_currencies],
    names=["transaction_date", "currency"]
).to_frame(index=False)

history_frame = history_grid.merge(
    ledger_history,
    on=["transaction_date", "currency"],
    how="left"
)

history_frame["net_flow"] = history_frame["net_flow"].fillna(0.0)
history_frame["weekday"] = pd.to_datetime(
    history_frame["transaction_date"]
).dt.weekday

weekday_baseline = (
    history_frame.groupby(["currency", "weekday"])["net_flow"]
    .mean()
    .to_dict()
)

forecast["forecast_weekday"] = pd.to_datetime(
    forecast["forecast_date"]
).dt.weekday

forecast["ledger_run_rate"] = [
    weekday_baseline.get(
        (row.currency, row.forecast_weekday),
        0.0
    )
    for row in forecast.itertuples()
]

forecast["run_rate_adjusted_net"] = (
    forecast["net_flow"] + forecast["ledger_run_rate"]
)

forecast["run_rate_adjusted_net_inr"] = (
    forecast["run_rate_adjusted_net"] * forecast["fx_to_inr"]
)


cash_position["fx_to_inr"] = cash_position["currency"].map(fx_to_inr)

if cash_position["fx_to_inr"].isna().any():
    st.error("Missing INR conversion rate for a bank-account currency.")
    st.stop()


cash_position["opening_cash_inr"] = (
    cash_position["opening_cash"] * cash_position["fx_to_inr"]
)

opening_cash_by_currency = dict(
    zip(cash_position["currency"], cash_position["opening_cash"])
)

all_forecast_dates = sorted(forecast["forecast_date"].unique())

currency_position_rows = []

for currency in sorted(forecast["currency"].unique()):

    opening_cash = float(opening_cash_by_currency[currency])

    daily_net = (
        forecast[forecast["currency"] == currency]
        .groupby("forecast_date")["net_flow"]
        .sum()
        .reindex(all_forecast_dates, fill_value=0.0)
    )

    running_cash = opening_cash

    for forecast_date, net_flow in daily_net.items():
        running_cash += float(net_flow)

        currency_position_rows.append({
            "forecast_date": forecast_date,
            "currency": currency,
            "opening_cash": opening_cash,
            "net_flow": float(net_flow),
            "projected_cash": running_cash,
        })


currency_positions = pd.DataFrame(currency_position_rows)

currency_positions["date_ordinal"] = pd.to_datetime(
    currency_positions["forecast_date"]
).map(pd.Timestamp.toordinal)

currency_positions["date_label"] = pd.to_datetime(
    currency_positions["forecast_date"]
).dt.strftime("%d %b")

currency_positions["fx_to_inr"] = (
    currency_positions["currency"].map(fx_to_inr)
)

currency_positions["projected_cash_crore"] = (
    currency_positions["projected_cash"]
    * currency_positions["fx_to_inr"]
    / 10_000_000
)


currency_summary = (
    currency_positions.groupby("currency", as_index=False)
    .agg(
        starting_cash=("opening_cash", "first"),
        lowest_projected_cash=("projected_cash", "min"),
        ending_projected_cash=("projected_cash", "last"),
        negative_balance_days=(
            "projected_cash",
            lambda values: int((values < 0).sum())
        ),
    )
)


shortfall = (
    forecast.assign(shortfall=forecast["net_flow"] < 0)
    .groupby("currency", as_index=False)
    .agg(
        forecast_days=("forecast_date", "count"),
        negative_days=("shortfall", "sum")
    )
)


daily_inr = (
    forecast.groupby("forecast_date", as_index=False)[
        ["inflow_inr", "outflow_inr", "net_flow_inr"]
    ]
    .sum()
    .sort_values("forecast_date")
)

model_daily = (
    forecast.groupby("forecast_date", as_index=False)[
        ["net_flow_inr", "run_rate_adjusted_net_inr"]
    ]
    .sum()
    .sort_values("forecast_date")
)


inr_inflow_total = daily_inr["inflow_inr"].sum()
inr_outflow_total = daily_inr["outflow_inr"].sum()
inr_net_total = daily_inr["net_flow_inr"].sum()

opening_cash_inr = cash_position["opening_cash_inr"].sum()

daily_position = daily_inr[
    ["forecast_date", "net_flow_inr"]
].copy()

daily_position["projected_cash_inr"] = (
    opening_cash_inr + daily_position["net_flow_inr"].cumsum()
)

lowest_projected_cash = min(
    opening_cash_inr,
    daily_position["projected_cash_inr"].min()
)

ending_projected_cash = daily_position[
    "projected_cash_inr"
].iloc[-1]


st.markdown(
    '<div class="section-kicker">LIVE LIQUIDITY SNAPSHOT · INR CONVERTED</div>',
    unsafe_allow_html=True
)

headline = st.columns(4)

headline[0].metric(
    "Starting cash",
    f"₹{opening_cash_inr:,.0f}"
)

headline[1].metric(
    "Forecast net flow",
    f"₹{inr_net_total:,.0f}"
)

headline[2].metric(
    "Lowest projected cash",
    f"₹{lowest_projected_cash:,.0f}"
)

headline[3].metric(
    "Ending projected cash",
    f"₹{ending_projected_cash:,.0f}"
)


st.caption(
    f"Cutoff: 10 Nov 2026 · Current view: {horizon} · "
    "FX rates are synthetic demo values"
)


with st.expander("Dataset inventory", expanded=False):

    inventory = st.columns(6)

    metric_labels = [
        ("Legal entities", "legal_entities"),
        ("Bank accounts", "bank_accounts"),
        ("Ledger entries", "ledger_entries"),
        ("Receivables", "receivables"),
        ("Payables", "payables"),
        ("Forecast rows", "cash_flow_forecasts"),
    ]

    for column, (label, key) in zip(inventory, metric_labels):
        column.metric(label, f"{counts[key]:,}")


overview_tab, forecast_tab, risk_tab, three_d_tab = st.tabs([
    "✦ Overview",
    "↗ Forecast Lab",
    "◉ Risk Monitor",
    "◇ 3D Liquidity"
])


# ============================================================
# OVERVIEW TAB
# ============================================================

with overview_tab:

    st.subheader("Projected liquidity in INR")

    position_metrics = st.columns(3)

    position_metrics[0].metric(
        "Starting cash",
        f"₹{opening_cash_inr:,.2f}"
    )

    position_metrics[1].metric(
        "Lowest projected cash",
        f"₹{lowest_projected_cash:,.2f}"
    )

    position_metrics[2].metric(
        "Ending projected cash",
        f"₹{ending_projected_cash:,.2f}"
    )

    overview_chart = px.area(
        daily_position,
        x="forecast_date",
        y="projected_cash_inr",
        labels={
            "forecast_date": "Forecast date",
            "projected_cash_inr": "Projected cash (INR)"
        },
        color_discrete_sequence=["#7868E8"],
    )

    overview_chart.add_hline(
        y=0,
        line_dash="dash",
        line_color="#E67583"
    )

    overview_chart.update_traces(
        line={"width": 3},
        fillcolor="rgba(120,104,232,.16)"
    )

    st.plotly_chart(
        overview_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )

    st.caption(
        "The position starts with balances through 9 Nov 2026 and then "
        "adds forecast cash flows. INR values use synthetic FX rates dated 1 Jan 2026."
    )

    st.download_button(
        "Download projected INR position CSV",
        data=daily_position.to_csv(index=False).encode("utf-8-sig"),
        file_name="yottaflex_projected_inr_position.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_inr_position",
    )

    st.subheader("Forecast movement by currency")

    compact = forecast.groupby(
        "currency",
        as_index=False
    )[["inflow", "outflow"]].sum()

    compact_chart = px.bar(
        compact.melt(
            id_vars="currency",
            var_name="flow_type",
            value_name="amount"
        ),
        x="currency",
        y="amount",
        color="flow_type",
        barmode="group",
        labels={
            "currency": "Currency",
            "amount": "Amount in source currency",
            "flow_type": "Flow"
        },
        color_discrete_map={
            "inflow": "#32B8A3",
            "outflow": "#F17B91"
        },
    )

    st.plotly_chart(
        compact_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )


# ============================================================
# FORECAST LAB TAB
# ============================================================

with forecast_tab:

    st.subheader("Forecast Lab")

    st.caption(
        "Explore date-wise cash flow and adjust the scenario assumptions in the sidebar."
    )

    source_summary = forecast.groupby(
        "currency",
        as_index=False
    )[["inflow", "outflow", "net_flow"]].sum()

    source_chart = px.bar(
        source_summary.melt(
            id_vars="currency",
            value_vars=["inflow", "outflow"],
            var_name="flow_type",
            value_name="amount"
        ),
        x="currency",
        y="amount",
        color="flow_type",
        barmode="group",
        labels={
            "currency": "Currency",
            "amount": "Amount in source currency",
            "flow_type": "Flow"
        },
        color_discrete_map={
            "inflow": "#32B8A3",
            "outflow": "#F17B91"
        },
    )

    # FIXED: Correct indentation and removed duplicate dataframe call.
    st.plotly_chart(
        source_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True},
        key="source_chart_secondary"
    )

    st.dataframe(
        source_summary.rename(columns={
            "currency": "Currency",
            "inflow": "Inflow",
            "outflow": "Outflow",
            "net_flow": "Net flow"
        }).style.format({
            "Inflow": "{:,.2f}",
            "Outflow": "{:,.2f}",
            "Net flow": "{:,.2f}"
        }),
        hide_index=True,
        use_container_width=True
    )

    st.subheader("Consolidated cash flow · INR")

    inr_flow_chart = px.line(
        daily_inr,
        x="forecast_date",
        y=["inflow_inr", "outflow_inr", "net_flow_inr"],
        markers=True,
        labels={
            "forecast_date": "Forecast date",
            "value": "Amount (INR)",
            "variable": "Flow"
        },
        color_discrete_map={
            "inflow_inr": "#32B8A3",
            "outflow_inr": "#F17B91",
            "net_flow_inr": "#7868E8"
        },
    )

    inr_flow_chart.add_hline(
        y=0,
        line_dash="dash",
        line_color="#9A96A8"
    )

    st.plotly_chart(
        inr_flow_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )

    st.subheader("90-day weekday run-rate baseline")

    st.caption(
        "Adds the average historical ledger movement for the matching "
        "weekday to the due-date forecast. This is a simple statistical baseline, "
        "not a trained model."
    )

    run_rate_chart = px.line(
        model_daily,
        x="forecast_date",
        y=["net_flow_inr", "run_rate_adjusted_net_inr"],
        markers=True,
        labels={
            "forecast_date": "Forecast date",
            "value": "Net flow (INR)",
            "variable": "Projection"
        },
        color_discrete_map={
            "net_flow_inr": "#9188A8",
            "run_rate_adjusted_net_inr": "#7868E8"
        },
    )

    run_rate_chart.add_hline(
        y=0,
        line_dash="dash",
        line_color="#9A96A8"
    )

    st.plotly_chart(
        run_rate_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )

    st.download_button(
        "Download run-rate baseline CSV",
        data=model_daily.to_csv(index=False).encode("utf-8-sig"),
        file_name="yottaflex_weekday_run_rate_baseline.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_run_rate_baseline",
    )

    st.subheader("What-if scenario comparison · INR")

    st.caption(
        "Delayed Receipt moves all forecast receipts 7 calendar days later. "
        "Stress reduces inflows by 10% and increases outflows by 20%. "
        "Delayed receipts remain visible after the selected forecast horizon."
    )

    scenario_settings = [
        ("Base Case", 1.0, 1.0, 0),
        ("Delayed Receipt", 1.0, 1.0, 7),
        ("Stress", 0.90, 1.20, 0),
        ("Upside", 1 + upside_inflow_pct / 100, 1 - upside_outflow_pct / 100, 0),
        ("Downside", 1 - downside_inflow_pct / 100, 1 + downside_outflow_pct / 100, 0),
    ]

    scenario_totals = []
    scenario_daily_rows = []
    for scenario_name, inflow_factor, outflow_factor, receipt_delay_days in scenario_settings:
        daily = daily_scenario(forecast, inflow_factor, outflow_factor, receipt_delay_days)
        daily["scenario"] = scenario_name
        daily["projected_cash_inr"] = opening_cash_inr + daily["net_flow_inr"].cumsum()
        scenario_daily_rows.append(daily)
        scenario_totals.append({
            "Scenario": scenario_name,
            "Receipt delay (days)": receipt_delay_days,
            "Inflow change": f"{(inflow_factor - 1) * 100:+.0f}%",
            "Outflow change": f"{(outflow_factor - 1) * 100:+.0f}%",
            "Inflows (INR)": daily["inflow_inr"].sum(),
            "Outflows (INR)": daily["outflow_inr"].sum(),
            "Net flow (INR)": daily["net_flow_inr"].sum(),
            "Lowest cash (INR)": min(opening_cash_inr, daily["projected_cash_inr"].min()),
        })

    st.dataframe(
        pd.DataFrame(scenario_totals).style.format({
            "Inflows (INR)": "₹{:,.2f}",
            "Outflows (INR)": "₹{:,.2f}",
            "Net flow (INR)": "₹{:,.2f}",
            "Lowest cash (INR)": "₹{:,.2f}"
        }),
        hide_index=True,
        use_container_width=True
    )

    scenario_daily = pd.concat(
        scenario_daily_rows,
        ignore_index=True
    )

    scenario_chart = px.line(
        scenario_daily,
        x="forecast_date",
        y="net_flow_inr",
        color="scenario",
        markers=True,
        labels={
            "forecast_date": "Forecast date",
            "net_flow_inr": "Net flow (INR)",
            "scenario": "Scenario"
        },
        color_discrete_map={
            "Base Case": "#7868E8",
            "Upside": "#32B8A3",
            "Downside": "#F17B91",
            "Delayed Receipt": "#D89124",
            "Stress": "#D64A5C",
        },
    )

    scenario_chart.add_hline(
        y=0,
        line_dash="dash",
        line_color="#9A96A8"
    )

    st.plotly_chart(
        scenario_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )

    st.caption(
        f"Current assumptions — Upside: inflows +{upside_inflow_pct}%, "
        f"outflows −{upside_outflow_pct}%; Downside: "
        f"inflows −{downside_inflow_pct}%, outflows +{downside_outflow_pct}%."
    )

    if st.button(
        f"Save these {len(scenario_settings)} scenario runs",
        type="primary",
        key="save_scenario_runs"
    ):
        try:
            saved_rows = save_scenario_runs(
                scenario_settings,
                scenario_daily
            )

            st.success(
                f"Saved {len(scenario_settings)} scenario runs and {saved_rows} daily INR forecast rows."
            )

        except Exception as error:
            st.error(f"Could not save scenario runs: {error}")

    export_columns = st.columns(2)

    export_columns[0].download_button(
        "Download forecast rows CSV",
        data=forecast.to_csv(index=False).encode("utf-8-sig"),
        file_name="yottaflex_forecast_rows.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_forecast_rows",
    )

    export_columns[1].download_button(
        "Download scenario comparison CSV",
        data=pd.DataFrame(scenario_totals).to_csv(
            index=False
        ).encode("utf-8-sig"),
        file_name="yottaflex_scenario_comparison.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_scenario_comparison",
    )


    with st.expander("Actual vs forecast"):
        actuals = compare_settlements(DB_PATH.resolve(), FORECAST_CUTOFF)
        if actuals.empty:
            st.info("Generate a fresh dataset to see synthetic settlements.")
        else:
            st.caption(
                "Full dataset, matched settlements only. Forecasts use cutoff FX. "
                "Actuals use the rate effective on the settlement date."
            )
            converted = actuals.dropna(subset=["forecast_fx", "actual_fx"])
            if len(converted) != len(actuals):
                st.warning(f"Missing FX rates for {len(actuals) - len(converted):,} settlements.")
            if not converted.empty:
                metrics = st.columns(3)
                metrics[0].metric("Matched settlements", f"{len(actuals):,}")
                metrics[1].metric("Late settlements", f"{actuals['days_late'].gt(0).sum():,}")
                metrics[2].metric("Net cash variance", f"₹{converted['net_variance_inr'].sum():,.2f}")
                planned = converted.groupby("forecast_date")["forecast_net_inr"].sum()
                settled = converted.groupby("settlement_date")["actual_net_inr"].sum()
                daily = pd.concat([planned.rename("Forecast"), settled.rename("Actual")], axis=1)
                dates = pd.date_range(daily.index.min(), daily.index.max()).strftime("%Y-%m-%d")
                st.line_chart(daily.reindex(dates).fillna(0), y_label="Net cash flow (INR)")
            st.dataframe(actuals.head(100), hide_index=True)
            st.download_button(
                "Download settlement comparison CSV",
                actuals.to_csv(index=False).encode("utf-8-sig"),
                file_name="yottaflex_settlement_comparison.csv",
                mime="text/csv",
            )


# ============================================================
# RISK MONITOR TAB
# ============================================================

with risk_tab:

    st.subheader("Risk Monitor")

    st.caption(
        "Currency exposures stay separate. Negative-flow days are warning "
        "indicators, not proof of insolvency."
    )

    left, right = st.columns(2)

    with left:

        st.markdown("#### Negative-flow days")

        st.dataframe(
            shortfall.rename(columns={
                "currency": "Currency",
                "forecast_days": "Forecast days",
                "negative_days": "Negative days"
            }),
            hide_index=True,
            use_container_width=True
        )

    with right:

        st.markdown("#### Overdue exposure")

        if overdue.empty:

            st.info("No overdue items found.")

        else:

            overdue_chart = px.bar(
                overdue,
                x="currency",
                y="amount",
                color="item_type",
                barmode="group",
                labels={
                    "currency": "Currency",
                    "amount": "Amount in source currency",
                    "item_type": "Overdue item"
                },
                color_discrete_map={
                    "Receivables": "#7868E8",
                    "Payables": "#F0B44C"
                },
            )

            st.plotly_chart(
                overdue_chart,
                use_container_width=True,
                config={"displaylogo": False, "scrollZoom": True}
            )

            st.dataframe(
                overdue.rename(columns={
                    "item_type": "Type",
                    "currency": "Currency",
                    "item_count": "Items",
                    "amount": "Exposure"
                }).style.format({
                    "Exposure": "{:,.2f}"
                }),
                hide_index=True,
                use_container_width=True
            )

    st.subheader("Projected cash by currency")

    st.dataframe(
        currency_summary.rename(columns={
            "currency": "Currency",
            "starting_cash": "Starting cash",
            "lowest_projected_cash": "Lowest projected cash",
            "ending_projected_cash": "Ending projected cash",
            "negative_balance_days": "Negative balance days",
        }).style.format({
            "Starting cash": "{:,.2f}",
            "Lowest projected cash": "{:,.2f}",
            "Ending projected cash": "{:,.2f}",
        }),
        hide_index=True,
        use_container_width=True
    )

    selected_currency = st.selectbox(
        "Choose a currency",
        sorted(currency_positions["currency"].unique())
    )

    selected_position = currency_positions[
        currency_positions["currency"] == selected_currency
    ]

    currency_chart = px.line(
        selected_position,
        x="forecast_date",
        y="projected_cash",
        markers=True,
        labels={
            "forecast_date": "Forecast date",
            "projected_cash": f"Projected cash ({selected_currency})"
        },
        color_discrete_sequence=["#7868E8"],
    )

    currency_chart.add_hline(
        y=0,
        line_dash="dash",
        line_color="#F17B91"
    )

    st.plotly_chart(
        currency_chart,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )

    risk_export = currency_summary.merge(
        shortfall,
        on="currency",
        how="left"
    )

    risk_downloads = st.columns(2)

    risk_downloads[0].download_button(
        "Download currency risk summary CSV",
        data=risk_export.to_csv(index=False).encode("utf-8-sig"),
        file_name="yottaflex_currency_risk_summary.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_risk_summary",
    )

    risk_downloads[1].download_button(
        "Download overdue exposure CSV",
        data=overdue.to_csv(index=False).encode("utf-8-sig"),
        file_name="yottaflex_overdue_exposure.csv",
        mime="text/csv",
        use_container_width=True,
        key="download_overdue_exposure",
    )


# ============================================================
# 3D LIQUIDITY TAB
# ============================================================

with three_d_tab:

    st.subheader("Liquidity landscape")

    st.caption(
        "Drag to rotate · scroll to zoom · hover over a line for date "
        "and projected balance."
    )

    currency_order = sorted(
        currency_positions["currency"].unique()
    )

    chart_colors = {
        "EUR": "#7868E8",
        "GBP": "#F17B91",
        "INR": "#32B8A3",
        "SGD": "#F0B44C",
        "USD": "#6289ED"
    }

    landscape = go.Figure()

    for currency_index, currency in enumerate(currency_order):

        currency_data = currency_positions[
            currency_positions["currency"] == currency
        ]

        landscape.add_trace(
            go.Scatter3d(
                x=currency_data["date_ordinal"],
                y=[currency_index] * len(currency_data),
                z=currency_data["projected_cash_crore"],
                customdata=currency_data[
                    ["date_label", "projected_cash"]
                ].to_numpy(),
                mode="lines+markers",
                name=currency,
                line={
                    "color": chart_colors.get(currency, "#7868E8"),
                    "width": 7
                },
                marker={
                    "color": chart_colors.get(currency, "#7868E8"),
                    "size": 4,
                    "opacity": .92
                },
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Date: %{customdata[0]}<br>"
                    "Projected balance: %{customdata[1]:,.2f} "
                    "%{fullData.name}<br>"
                    "INR equivalent: ₹%{z:,.2f} crore"
                    "<extra></extra>"
                ),
            )
        )

    all_dates = sorted(
        currency_positions["date_ordinal"].unique()
    )

    date_labels = (
        currency_positions
        .drop_duplicates("date_ordinal")
        .set_index("date_ordinal")["date_label"]
        .to_dict()
    )

    tick_step = max(1, len(all_dates) // 7)

    tick_values = all_dates[::tick_step]

    if all_dates[-1] not in tick_values:
        tick_values.append(all_dates[-1])

    landscape.update_layout(
        height=620,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        legend={
            "title": "Currency",
            "bgcolor": "rgba(255,255,255,.78)"
        },
        scene={
            "bgcolor": "#FBFAFF",
            "xaxis": {
                "title": "Forecast date",
                "tickmode": "array",
                "tickvals": tick_values,
                "ticktext": [
                    date_labels[value]
                    for value in tick_values
                ],
                "gridcolor": "#E8E4F2"
            },
            "yaxis": {
                "title": "Currency",
                "tickmode": "array",
                "tickvals": list(range(len(currency_order))),
                "ticktext": currency_order,
                "gridcolor": "#E8E4F2"
            },
            "zaxis": {
                "title": "Projected balance (₹ crore)",
                "gridcolor": "#E8E4F2"
            },
            "camera": {
                "eye": {"x": 1.55, "y": 1.65, "z": 1.15}
            },
            "aspectmode": "auto",
        },
    )

    st.plotly_chart(
        landscape,
        use_container_width=True,
        config={"displaylogo": False, "scrollZoom": True}
    )
