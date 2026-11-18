"""Lightweight schema validation for downloaded source datasets."""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

EXPECTED = {
    "hies_state.csv": {"date", "state", "income_mean", "income_median", "expenditure_mean", "gini", "poverty"},
    "hh_income_state.csv": {"date", "state", "income_mean", "income_median"},
    "cpi_state.csv": {"date", "state", "division", "index"},
    "formal_wages_state.csv": {"date", "state", "employees", "wages_median"},
}

def validate_file(path: Path, expected_columns: set[str]) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}. Run src/fetch_data.py first.")
    df = pd.read_csv(path)
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"{path.name}: missing columns {sorted(missing)}")
    if df.empty:
        raise ValueError(f"{path.name}: dataset is empty")
    if "date" in df.columns:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        if parsed.isna().any():
            raise ValueError(f"{path.name}: contains unparseable dates")

def main() -> None:
    for filename, expected in EXPECTED.items():
        validate_file(RAW / filename, expected)
        print(f"OK: {filename}")

if __name__ == "__main__":
    main()
