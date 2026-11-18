from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from build_indicators import build_household_metrics, build_wage_pulse


# -----------------------------
# App configuration
# -----------------------------
st.set_page_config(
    page_title="Malaysia Household Resilience Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2.5rem;}
    .small-note {color: #64748b; font-size: 0.88rem; line-height: 1.45;}
    .policy-box {
        border: 1px solid #dbe4ee;
        border-radius: 12px;
        padding: 1rem 1.1rem;
        background: #f8fafc;
        margin-bottom: 0.8rem;
    }
    .policy-box strong {color: #0f172a;}
    div[data-testid="stMetric"] {
        border: 1px solid #e2e8f0;
        padding: 0.75rem;
        border-radius: 10px;
        background: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_URLS = {
    "hies": "https://storage.dosm.gov.my/hies/hies_state.csv",
    "cpi": "https://storage.dosm.gov.my/cpi/cpi_2d_state.csv",
    "wages": "https://storage.dosm.gov.my/labour/formal_wages_state.csv",
}

TRIAGE_LABELS = {
    "higher_attention": "Higher attention",
    "watch": "Watch",
    "relatively_resilient": "Relatively resilient",
}

TRIAGE_ORDER = ["Higher attention", "Watch", "Relatively resilient"]


def pct(x: float | int | None, digits: int = 1) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x) * 100:.{digits}f}%"


def rm(x: float | int | None) -> str:
    if pd.isna(x):
        return "—"
    return f"RM {float(x):,.0f}"


def num(x: float | int | None, digits: int = 2) -> str:
    if pd.isna(x):
        return "—"
    return f"{float(x):.{digits}f}"


@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def load_metrics() -> tuple[pd.DataFrame, str]:
    """Load locally processed data when available; otherwise build from official sources."""
    processed = ROOT / "data" / "processed" / "state_resilience_metrics.csv"

    if processed.exists():
        df = pd.read_csv(processed)
        if "wage_latest_date" in df.columns:
            df["wage_latest_date"] = pd.to_datetime(df["wage_latest_date"], errors="coerce")
        return df, "Local processed file"

    hies = pd.read_csv(DATA_URLS["hies"])
    cpi = pd.read_csv(DATA_URLS["cpi"])
    wages = pd.read_csv(DATA_URLS["wages"])

    household = build_household_metrics(hies, cpi)
    wage = build_wage_pulse(wages)

    combined = household.merge(
        wage[[
            "state",
            "wages_median_latest",
            "wages_median_prior_year",
            "wage_yoy_growth",
            "wage_latest_date",
        ]],
        on="state",
        how="left",
    )
    return combined, "Built live from official DOSM/data.gov.my sources"


@st.cache_data(show_spinner=False)
def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


try:
    with st.spinner("Loading official Malaysian household resilience indicators..."):
        df, data_mode = load_metrics()
except Exception as exc:
    st.error("The app could not load the analytical data.")
    st.code(str(exc))
    st.markdown(
        "Run the local pipeline first with `python src/fetch_data.py` and "
        "`python src/build_indicators.py`, then restart Streamlit."
    )
    st.stop()

if df.empty:
    st.error("No analytical records were produced.")
    st.stop()

# Friendly labels used throughout the UI.
df = df.copy()
df["triage_label"] = df["policy_triage"].map(TRIAGE_LABELS).fillna(df["policy_triage"])
df["triage_label"] = pd.Categorical(df["triage_label"], TRIAGE_ORDER, ordered=True)

latest_hies_year = int(df["latest_year"].dropna().max()) if "latest_year" in df else None
previous_hies_year = int(df["previous_year"].dropna().max()) if "previous_year" in df else None
latest_wage_date = pd.to_datetime(df["wage_latest_date"], errors="coerce").max() if "wage_latest_date" in df else pd.NaT

# -----------------------------
# Sidebar navigation
# -----------------------------
st.sidebar.title("Household Resilience Monitor")
st.sidebar.caption("Malaysia · public-policy data science portfolio")

page = st.sidebar.radio(
    "Explore",
    [
        "National overview",
        "State profile",
        "Income & inflation",
        "Poverty & inequality",
        "Formal wage pulse",
        "Policy triage lab",
        "Methodology & limitations",
    ],
)

states = sorted(df["state"].dropna().unique())
default_state = "Malaysia" if "Malaysia" in states else states[0]
selected_state = st.sidebar.selectbox(
    "State / territory",
    states,
    index=states.index(default_state),
)

st.sidebar.divider()
st.sidebar.markdown("**Data status**")
st.sidebar.caption(data_mode)
if latest_hies_year:
    st.sidebar.caption(f"HIES comparison: {previous_hies_year} → {latest_hies_year}")
if pd.notna(latest_wage_date):
    st.sidebar.caption(f"Latest formal wage month: {latest_wage_date:%b %Y}")

st.sidebar.download_button(
    "Download analytical table",
    data=csv_bytes(df.drop(columns=["triage_label"], errors="ignore")),
    file_name="state_resilience_metrics.csv",
    mime="text/csv",
    use_container_width=True,
)

# -----------------------------
# Header
# -----------------------------
st.title("Malaysia Household Resilience Monitor")
st.caption(
    "A reproducible policy-data dashboard integrating household income, living-cost, poverty, "
    "inequality and formal-wage signals from official Malaysian public data."
)

st.markdown(
    """
    <div class="policy-box">
    <strong>Policy question:</strong> Are household incomes across Malaysian states keeping pace with living costs, and where do multiple indicators suggest a need for closer policy attention?
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Page: National overview
# -----------------------------
if page == "National overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("States / territories", f"{df['state'].nunique()}")
    c2.metric("Median real income growth", pct(df["real_median_income_growth"].median()))
    c3.metric("Median poverty rate", f"{df['poverty_latest'].median():.1f}%")
    c4.metric("Higher-attention flags", int((df["policy_triage"] == "higher_attention").sum()))

    left, right = st.columns([1.25, 1])

    with left:
        st.subheader("Poverty and real household-income growth")
        fig = px.scatter(
            df,
            x="real_median_income_growth",
            y="poverty_latest",
            color="triage_label",
            hover_name="state",
            hover_data={
                "real_median_income_growth": ":.2%",
                "poverty_latest": ":.1f",
                "gini_latest": ":.3f",
                "triage_label": True,
            },
            category_orders={"triage_label": TRIAGE_ORDER},
            labels={
                "real_median_income_growth": "Real median household income growth",
                "poverty_latest": "Poverty rate (%)",
                "triage_label": "Policy triage",
            },
        )
        fig.add_vline(x=df["real_median_income_growth"].median(), line_dash="dash", line_width=1)
        fig.add_hline(y=df["poverty_latest"].median(), line_dash="dash", line_width=1)
        fig.update_layout(legend_title_text="Policy triage")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Dashed lines show the cross-state medians used in the baseline screening rule.")

    with right:
        st.subheader("Baseline triage")
        triage_counts = (
            df["triage_label"]
            .value_counts()
            .reindex(TRIAGE_ORDER)
            .fillna(0)
            .rename_axis("Category")
            .reset_index(name="States")
        )
        fig2 = px.bar(triage_counts, x="Category", y="States", text="States")
        fig2.update_layout(showlegend=False, xaxis_title="", yaxis_title="Number of states / territories")
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**How to read the triage**")
        st.markdown(
            "- **Higher attention:** above-median poverty and below-median real income growth.\n"
            "- **Watch:** one of those two conditions is met.\n"
            "- **Relatively resilient:** neither condition is met."
        )
        st.info("This is a screening device, not an official vulnerability ranking.")

    st.subheader("Real median household-income growth by state")
    ranked = df.sort_values("real_median_income_growth")
    fig3 = px.bar(
        ranked,
        x="real_median_income_growth",
        y="state",
        orientation="h",
        color="triage_label",
        category_orders={"triage_label": TRIAGE_ORDER},
        labels={
            "real_median_income_growth": "Real median household income growth",
            "state": "",
            "triage_label": "Policy triage",
        },
    )
    fig3.update_xaxes(tickformat=".1%")
    st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# Page: State profile
# -----------------------------
elif page == "State profile":
    row = df[df["state"].eq(selected_state)].iloc[0]
    st.subheader(selected_state)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Median household income", rm(row["median_income_latest"]))
    m2.metric("Real income growth", pct(row["real_median_income_growth"]))
    m3.metric("Poverty rate", f"{row['poverty_latest']:.1f}%")
    m4.metric("Gini coefficient", num(row["gini_latest"], 3))

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Nominal income growth", pct(row["nominal_income_growth"]))
    m6.metric("Inflation between HIES years", pct(row["inflation_between_hies"]))
    m7.metric("Expenditure / income", pct(row["expenditure_to_income_ratio"]))
    m8.metric("Formal wage YoY growth", pct(row.get("wage_yoy_growth", np.nan)))

    st.markdown(
        f"""
        <div class="policy-box">
        <strong>Baseline triage:</strong> {TRIAGE_LABELS.get(row['policy_triage'], row['policy_triage'])}.<br>
        <span class="small-note">This category is generated from a transparent cross-state screening rule and should trigger further analysis, not a final policy conclusion.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("State versus cross-state median")
    comp = pd.DataFrame(
        {
            "Indicator": [
                "Real income growth",
                "Poverty rate",
                "Expenditure / income",
                "Formal wage growth",
            ],
            selected_state: [
                row["real_median_income_growth"],
                row["poverty_latest"] / 100,
                row["expenditure_to_income_ratio"],
                row.get("wage_yoy_growth", np.nan),
            ],
            "Cross-state median": [
                df["real_median_income_growth"].median(),
                df["poverty_latest"].median() / 100,
                df["expenditure_to_income_ratio"].median(),
                df["wage_yoy_growth"].median() if "wage_yoy_growth" in df else np.nan,
            ],
        }
    )
    long = comp.melt(id_vars="Indicator", var_name="Series", value_name="Value")
    fig = px.bar(long, x="Indicator", y="Value", color="Series", barmode="group")
    fig.update_yaxes(tickformat=".1%")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Interpretation prompts"):
        st.markdown(
            """
            - Is the state's nominal income growth still strong after adjusting for CPI?
            - Does the poverty signal tell the same story as the income-growth signal?
            - Is expenditure pressure unusually high relative to other states?
            - Does the higher-frequency formal wage signal move in the same direction as household income?
            - Which household groups or districts would need to be examined before making a policy recommendation?
            """
        )

# -----------------------------
# Page: Income & inflation
# -----------------------------
elif page == "Income & inflation":
    st.subheader("From nominal growth to purchasing-power growth")
    chart_df = df[[
        "state",
        "nominal_income_growth",
        "inflation_between_hies",
        "real_median_income_growth",
    ]].copy()
    long = chart_df.melt(id_vars="state", var_name="Indicator", value_name="Rate")
    indicator_names = {
        "nominal_income_growth": "Nominal median income growth",
        "inflation_between_hies": "CPI increase",
        "real_median_income_growth": "Real median income growth",
    }
    long["Indicator"] = long["Indicator"].map(indicator_names)

    focus = st.multiselect(
        "States to compare",
        states,
        default=[selected_state] if selected_state in states else states[:1],
    )
    if focus:
        fig = px.bar(
            long[long["state"].isin(focus)],
            x="state",
            y="Rate",
            color="Indicator",
            barmode="group",
        )
        fig.update_yaxes(tickformat=".1%")
        fig.update_layout(xaxis_title="", yaxis_title="Rate")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Real growth formula**")
    st.code("real growth = (1 + nominal income growth) / (1 + inflation) - 1")
    st.caption("The calculation is multiplicative; it does not simply subtract inflation from nominal growth.")

    st.subheader("All states")
    display = df[[
        "state",
        "median_income_previous",
        "median_income_latest",
        "nominal_income_growth",
        "inflation_between_hies",
        "real_median_income_growth",
    ]].sort_values("real_median_income_growth")
    st.dataframe(
        display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "state": "State",
            "median_income_previous": st.column_config.NumberColumn("Previous median income", format="RM %.0f"),
            "median_income_latest": st.column_config.NumberColumn("Latest median income", format="RM %.0f"),
            "nominal_income_growth": st.column_config.NumberColumn("Nominal growth", format="%.1f%%"),
            "inflation_between_hies": st.column_config.NumberColumn("CPI increase", format="%.1f%%"),
            "real_median_income_growth": st.column_config.NumberColumn("Real growth", format="%.1f%%"),
        },
    )

# -----------------------------
# Page: Poverty & inequality
# -----------------------------
elif page == "Poverty & inequality":
    st.subheader("Poverty, inequality and income resilience")
    fig = px.scatter(
        df,
        x="gini_latest",
        y="poverty_latest",
        size="median_income_latest",
        color="real_median_income_growth",
        hover_name="state",
        labels={
            "gini_latest": "Gini coefficient",
            "poverty_latest": "Poverty rate (%)",
            "median_income_latest": "Median household income",
            "real_median_income_growth": "Real income growth",
        },
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Bubble size represents latest median household income. Colour represents real median household-income growth.")

    cols = st.columns(2)
    with cols[0]:
        p = df.sort_values("poverty_latest")
        fig2 = px.bar(p, x="poverty_latest", y="state", orientation="h")
        fig2.update_layout(xaxis_title="Poverty rate (%)", yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)
    with cols[1]:
        g = df.sort_values("gini_latest")
        fig3 = px.bar(g, x="gini_latest", y="state", orientation="h")
        fig3.update_layout(xaxis_title="Gini coefficient", yaxis_title="")
        st.plotly_chart(fig3, use_container_width=True)

    st.warning(
        "State averages can conceal large within-state differences. Distributional or household-type analysis is needed before targeting interventions."
    )

# -----------------------------
# Page: Formal wage pulse
# -----------------------------
elif page == "Formal wage pulse":
    st.subheader("Formal wages as a separate, higher-frequency signal")
    wage_df = df.dropna(subset=["wage_yoy_growth"]).copy()

    if wage_df.empty:
        st.info("Formal wage growth is not available in the current analytical table.")
    else:
        corr = wage_df[["wage_yoy_growth", "real_median_income_growth"]].corr().iloc[0, 1]
        c1, c2 = st.columns([1, 3])
        c1.metric("Descriptive correlation", f"{corr:.2f}")
        c1.caption("Correlation is descriptive only; it is not evidence of causality.")

        with c2:
            fig = px.scatter(
                wage_df,
                x="wage_yoy_growth",
                y="real_median_income_growth",
                hover_name="state",
                trendline=None,
                labels={
                    "wage_yoy_growth": "Formal-sector median wage growth",
                    "real_median_income_growth": "Real median household-income growth",
                },
            )
            fig.update_xaxes(tickformat=".1%")
            fig.update_yaxes(tickformat=".1%")
            st.plotly_chart(fig, use_container_width=True)

        ranked = wage_df.sort_values("wage_yoy_growth")
        fig2 = px.bar(
            ranked,
            x="wage_yoy_growth",
            y="state",
            orientation="h",
            labels={"wage_yoy_growth": "Formal-sector median wage growth", "state": ""},
        )
        fig2.update_xaxes(tickformat=".1%")
        st.plotly_chart(fig2, use_container_width=True)

        st.info(
            "Formal employee wages and household income measure different concepts. The comparison is useful as a consistency check, not as a substitution."
        )

# -----------------------------
# Page: Policy triage lab
# -----------------------------
elif page == "Policy triage lab":
    st.subheader("Sensitivity lab: how analytical choices change the screening result")
    st.caption(
        "This page deliberately exposes the assumptions behind policy triage. Adjust the thresholds to see how many states change category."
    )

    c1, c2, c3 = st.columns(3)
    poverty_q = c1.slider("Poverty percentile threshold", 0.25, 0.75, 0.50, 0.05)
    growth_q = c2.slider("Real-growth percentile threshold", 0.25, 0.75, 0.50, 0.05)
    include_expenditure = c3.toggle("Require high expenditure pressure", value=False)

    poverty_cut = df["poverty_latest"].quantile(poverty_q)
    growth_cut = df["real_median_income_growth"].quantile(growth_q)
    expenditure_cut = df["expenditure_to_income_ratio"].median()

    high_poverty = df["poverty_latest"] > poverty_cut
    weak_growth = df["real_median_income_growth"] < growth_cut
    high_expenditure = df["expenditure_to_income_ratio"] > expenditure_cut

    if include_expenditure:
        higher_attention = high_poverty & weak_growth & high_expenditure
        watch = (high_poverty.astype(int) + weak_growth.astype(int) + high_expenditure.astype(int)) >= 2
    else:
        higher_attention = high_poverty & weak_growth
        watch = high_poverty | weak_growth

    scenario = df[[
        "state",
        "poverty_latest",
        "real_median_income_growth",
        "expenditure_to_income_ratio",
        "policy_triage",
    ]].copy()
    scenario["scenario_triage"] = np.select(
        [higher_attention, watch],
        ["Higher attention", "Watch"],
        default="Relatively resilient",
    )
    scenario["baseline_triage"] = scenario["policy_triage"].map(TRIAGE_LABELS)
    scenario["changed"] = scenario["scenario_triage"] != scenario["baseline_triage"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Poverty cutoff", f"{poverty_cut:.1f}%")
    m2.metric("Real-growth cutoff", pct(growth_cut))
    m3.metric("States changing category", int(scenario["changed"].sum()))

    st.dataframe(
        scenario.sort_values(["scenario_triage", "state"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "state": "State",
            "poverty_latest": st.column_config.NumberColumn("Poverty rate", format="%.1f%%"),
            "real_median_income_growth": st.column_config.NumberColumn("Real income growth", format="%.1f%%"),
            "expenditure_to_income_ratio": st.column_config.NumberColumn("Expenditure / income", format="%.1f%%"),
            "policy_triage": None,
            "baseline_triage": "Baseline",
            "scenario_triage": "Sensitivity scenario",
            "changed": "Changed?",
        },
    )

    st.markdown(
        """
        <div class="policy-box">
        <strong>Analytical judgement:</strong> A screening result is partly a function of threshold choice. The correct response is not to hide that sensitivity, but to test it, document it and avoid presenting a threshold-dependent flag as a causal finding.
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Page: Methodology & limitations
# -----------------------------
elif page == "Methodology & limitations":
    st.subheader("Methodology")
    st.markdown(
        """
        **Primary indicators**

        1. **Nominal median household-income growth** between the latest two HIES years.
        2. **State CPI change** using annual-average `overall` CPI.
        3. **Real median household-income growth** calculated as:

           `real growth = (1 + nominal growth) / (1 + inflation) - 1`

        4. **Expenditure pressure** = mean household expenditure / mean household income.
        5. **Poverty and Gini** retained as separate distributional indicators.
        6. **Formal wage pulse** retained as a separate administrative labour-market signal.
        """
    )

    st.subheader("Why the model stays simple")
    st.markdown(
        "The unit of analysis is the state / Federal Territory, so the number of observations is small. "
        "The analytical problem is transparent comparison and triage, not prediction. A more complex model "
        "could create apparent sophistication without improving the policy decision."
    )

    st.subheader("Evidence boundaries")
    st.markdown(
        """
        - HIES estimates are survey statistics, not administrative counts.
        - State CPI is an average basket; individual households face different consumption patterns.
        - Formal-sector wages exclude self-employed, gig and other non-formal workers.
        - Household income and employee wages are conceptually different.
        - State-level analysis cannot identify within-state household heterogeneity.
        - Correlation is not causation; this project does not estimate programme impacts or the causal effect of inflation.
        - The baseline triage is a reproducible screening rule, not an official vulnerability index.
        """
    )

    st.subheader("Official sources")
    st.markdown(
        """
        - [Household Income and Expenditure: States](https://open.dosm.gov.my/data-catalogue/hies_state)
        - [Monthly CPI by State & Division](https://open.dosm.gov.my/data-catalogue/cpi_state)
        - [Monthly Formal Sector Wages by State](https://open.dosm.gov.my/data-catalogue/formal_wages_state)
        """
    )

    st.subheader("Reproducibility")
    st.markdown(
        "The Streamlit interface is only the presentation layer. The repository retains the standalone "
        "data-acquisition, validation, indicator-building, visualisation, notebook, tests and R replication workflows."
    )

st.divider()
st.caption(
    "Portfolio project by Farah Ainaa Baharudin · Public official data only · "
    "Evidence is presented for analytical screening and policy research, not as an official KRI or government product."
)
