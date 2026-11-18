import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from build_indicators import real_growth, build_household_metrics

def test_real_growth_identity():
    assert real_growth(0.10, 0.10) == pytest.approx(0.0)

def test_real_growth_positive():
    assert real_growth(0.12, 0.04) == pytest.approx((1.12 / 1.04) - 1)

def test_policy_triage_is_transparent():
    hies = pd.DataFrame({
        "date": ["2022-01-01","2024-01-01","2022-01-01","2024-01-01"],
        "state": ["A","A","B","B"],
        "income_mean": [5000,5500,7000,8400],
        "income_median": [4000,4200,6000,7200],
        "expenditure_mean": [3500,4000,4000,4500],
        "gini": [0.40,0.41,0.30,0.29],
        "poverty": [12.0,11.0,2.0,1.5],
    })
    cpi = pd.DataFrame({
        "date": ["2022-01-01","2024-01-01","2022-01-01","2024-01-01"],
        "state": ["A","A","B","B"],
        "division": ["overall"]*4,
        "index": [100,108,100,104],
    })
    result = build_household_metrics(hies, cpi).set_index("state")
    assert set(result["policy_triage"]).issubset(
        {"higher_attention", "watch", "relatively_resilient"}
    )
    assert result.loc["A", "real_median_income_growth"] < result.loc["B", "real_median_income_growth"]
