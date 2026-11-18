"""Construct transparent state-level household resilience indicators."""

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

def real_growth(nominal_growth: pd.Series | float, inflation: pd.Series | float):
    """Convert nominal growth and inflation rates into real growth."""
    return (1 + nominal_growth) / (1 + inflation) - 1

def annual_overall_cpi(cpi: pd.DataFrame) -> pd.DataFrame:
    df = cpi.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["division"].eq("overall")].copy()
    df["year"] = df["date"].dt.year
    return (
        df.groupby(["state", "year"], as_index=False)["index"]
        .mean()
        .rename(columns={"index": "cpi_annual"})
    )

def latest_two_hies_years(hies: pd.DataFrame) -> tuple[int, int]:
    years = sorted(pd.to_datetime(hies["date"]).dt.year.unique())
    if len(years) < 2:
        raise ValueError("Need at least two HIES years.")
    return years[-2], years[-1]

def build_household_metrics(hies: pd.DataFrame, cpi: pd.DataFrame) -> pd.DataFrame:
    h = hies.copy()
    h["date"] = pd.to_datetime(h["date"])
    h["year"] = h["date"].dt.year

    previous_year, latest_year = latest_two_hies_years(h)
    h = h[h["year"].isin([previous_year, latest_year])].copy()

    income = h.pivot(index="state", columns="year", values="income_median")
    mean_income = h.pivot(index="state", columns="year", values="income_mean")
    expenditure = h.pivot(index="state", columns="year", values="expenditure_mean")
    poverty = h.pivot(index="state", columns="year", values="poverty")
    gini = h.pivot(index="state", columns="year", values="gini")

    cpi_annual = annual_overall_cpi(cpi)
    cpi_p = cpi_annual.pivot(index="state", columns="year", values="cpi_annual")

    common = income.index.intersection(cpi_p.index)
    out = pd.DataFrame(index=common)

    out["previous_year"] = previous_year
    out["latest_year"] = latest_year
    out["median_income_previous"] = income.loc[common, previous_year]
    out["median_income_latest"] = income.loc[common, latest_year]
    out["nominal_income_growth"] = (
        out["median_income_latest"] / out["median_income_previous"] - 1
    )

    out["cpi_previous"] = cpi_p.loc[common, previous_year]
    out["cpi_latest"] = cpi_p.loc[common, latest_year]
    out["inflation_between_hies"] = out["cpi_latest"] / out["cpi_previous"] - 1
    out["real_median_income_growth"] = real_growth(
        out["nominal_income_growth"], out["inflation_between_hies"]
    )

    out["mean_income_latest"] = mean_income.loc[common, latest_year]
    out["mean_expenditure_latest"] = expenditure.loc[common, latest_year]
    out["expenditure_to_income_ratio"] = (
        out["mean_expenditure_latest"] / out["mean_income_latest"]
    )
    out["poverty_latest"] = poverty.loc[common, latest_year]
    out["poverty_change_pp"] = poverty.loc[common, latest_year] - poverty.loc[common, previous_year]
    out["gini_latest"] = gini.loc[common, latest_year]
    out["gini_change"] = gini.loc[common, latest_year] - gini.loc[common, previous_year]

    out = out.reset_index()

    poverty_cut = out["poverty_latest"].median()
    growth_cut = out["real_median_income_growth"].median()

    high_poverty = out["poverty_latest"] > poverty_cut
    weak_growth = out["real_median_income_growth"] < growth_cut

    out["policy_triage"] = np.select(
        [high_poverty & weak_growth, high_poverty | weak_growth],
        ["higher_attention", "watch"],
        default="relatively_resilient",
    )
    return out

def build_wage_pulse(wages: pd.DataFrame) -> pd.DataFrame:
    w = wages.copy()
    w["date"] = pd.to_datetime(w["date"])
    latest_date = w["date"].max()
    prior_date = latest_date - pd.DateOffset(years=1)

    latest = w[w["date"].eq(latest_date)][["state", "wages_median", "employees"]].copy()
    latest = latest.rename(columns={
        "wages_median": "wages_median_latest",
        "employees": "employees_latest",
    })

    prior = w[w["date"].eq(prior_date)][["state", "wages_median"]].copy()
    prior = prior.rename(columns={"wages_median": "wages_median_prior_year"})

    out = latest.merge(prior, on="state", how="left")
    out["wage_yoy_growth"] = (
        out["wages_median_latest"] / out["wages_median_prior_year"] - 1
    )
    out["wage_latest_date"] = latest_date
    return out

def main() -> None:
    hies = pd.read_csv(RAW / "hies_state.csv")
    cpi = pd.read_csv(RAW / "cpi_state.csv")
    wages = pd.read_csv(RAW / "formal_wages_state.csv")

    household = build_household_metrics(hies, cpi)
    wage = build_wage_pulse(wages)

    combined = household.merge(
        wage[["state", "wages_median_latest", "wages_median_prior_year",
              "wage_yoy_growth", "wage_latest_date"]],
        on="state",
        how="left",
    )

    out = PROCESSED / "state_resilience_metrics.csv"
    combined.to_csv(out, index=False)
    print(f"Saved {len(combined)} state records to {out}")

if __name__ == "__main__":
    main()
