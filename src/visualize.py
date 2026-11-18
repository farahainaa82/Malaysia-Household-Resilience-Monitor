"""Create policy-oriented figures from the processed indicators."""

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "state_resilience_metrics.csv"
FIG_DIR = ROOT / "reports" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

def save_bar(df, value, title, filename, percent=False):
    plot_df = df.sort_values(value).copy()
    values = plot_df[value] * 100 if percent else plot_df[value]

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(plot_df["state"], values)
    ax.set_title(title)
    ax.set_xlabel("Percent" if percent else value.replace("_", " ").title())
    ax.grid(axis="x", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, dpi=180)
    plt.close(fig)

def main() -> None:
    df = pd.read_csv(DATA)

    save_bar(
        df,
        "real_median_income_growth",
        "Real Median Household Income Growth Between Latest HIES Years",
        "01_real_income_growth.png",
        percent=True,
    )

    save_bar(
        df,
        "expenditure_to_income_ratio",
        "Mean Household Expenditure Relative to Mean Household Income",
        "02_expenditure_pressure.png",
        percent=True,
    )

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(df["real_median_income_growth"] * 100, df["poverty_latest"])
    for _, row in df.iterrows():
        ax.annotate(
            row["state"],
            (row["real_median_income_growth"] * 100, row["poverty_latest"]),
            fontsize=7,
            xytext=(3, 3),
            textcoords="offset points",
        )
    ax.axvline(df["real_median_income_growth"].median() * 100, linestyle="--", linewidth=1)
    ax.axhline(df["poverty_latest"].median(), linestyle="--", linewidth=1)
    ax.set_xlabel("Real median household income growth (%)")
    ax.set_ylabel("Latest poverty rate (%)")
    ax.set_title("Policy Triage: Poverty and Real Income Growth")
    ax.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_policy_triage.png", dpi=180)
    plt.close(fig)

    wage_df = df.dropna(subset=["wage_yoy_growth"]).copy()
    save_bar(
        wage_df,
        "wage_yoy_growth",
        "Latest Formal-Sector Median Wage Growth, Year on Year",
        "04_formal_wage_growth.png",
        percent=True,
    )

    print(f"Figures saved to {FIG_DIR}")

if __name__ == "__main__":
    main()
