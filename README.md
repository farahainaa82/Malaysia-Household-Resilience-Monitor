# Malaysia Household Resilience Monitor

**A reproducible public-policy data science portfolio project using official Malaysian open data**

This project asks a simple policy question:

> **Are household incomes across Malaysian states keeping pace with living costs, and where do income, expenditure, poverty and wage signals point to greater policy attention?**

The repository is designed as a writing-and-code portfolio for the **Khazanah Research Institute (KRI) – Policy Researcher (Data Science)** application.

## Why this question matters

Nominal income growth can look positive while purchasing power changes little once inflation is considered. At the same time, state averages can hide important differences in poverty, expenditure pressure, inequality and labour-market wages.

This project does **not** create an official vulnerability score. Instead, it uses transparent, reproducible indicators to support policy triage and to show where deeper analysis may be warranted.

## What the project demonstrates

- programmatic acquisition of Malaysian public data;
- schema validation and reproducible data preparation;
- joining survey and administrative datasets with different frequencies;
- inflation adjustment and transparent indicator construction;
- explicit treatment of analytical limitations;
- policy-oriented visualisation;
- automated tests for core calculations;
- an independent R replication of the main real-income calculation;
- clear separation between **evidence**, **interpretation**, and **policy implication**.

## Official data sources

All data are public and sourced from the Department of Statistics Malaysia (DOSM) / data.gov.my.

1. **Household Income and Expenditure: States**
   - Income, expenditure, Gini coefficient and poverty rate by state.
   - https://open.dosm.gov.my/data-catalogue/hies_state
   - Raw CSV: `https://storage.dosm.gov.my/hies/hies_state.csv`

2. **Household Income by State**
   - Long-run mean and median household income by state.
   - https://open.dosm.gov.my/data-catalogue/hh_income_state
   - Raw CSV: `https://storage.dosm.gov.my/hies/hh_income_state.csv`

3. **Monthly CPI by State & Division**
   - State-level CPI; the analysis uses the `overall` division.
   - https://open.dosm.gov.my/data-catalogue/cpi_state
   - Raw CSV: `https://storage.dosm.gov.my/cpi/cpi_2d_state.csv`

4. **Monthly Formal Sector Wages by State**
   - Formal-sector employment and median monthly wages by state.
   - https://open.dosm.gov.my/data-catalogue/formal_wages_state
   - Raw CSV: `https://storage.dosm.gov.my/labour/formal_wages_state.csv`

The source datasets are made available under **CC BY 4.0**. This repository does not redistribute the raw datasets; the pipeline downloads them from the official sources.

## Analytical design

The main state-level indicators are:

### 1. Nominal median household income growth
For the latest two HIES years:

`nominal growth = income_latest / income_previous - 1`

### 2. Inflation between HIES years
Monthly state CPI is converted to an annual average for the two HIES years:

`inflation = annual_CPI_latest / annual_CPI_previous - 1`

### 3. Real median household income growth
The inflation-adjusted change is calculated multiplicatively:

`real growth = (1 + nominal growth) / (1 + inflation) - 1`

This avoids subtracting percentage rates directly.

### 4. Expenditure pressure
A descriptive ratio:

`mean household expenditure / mean household income`

It is **not** interpreted as a household savings rate because income and expenditure are survey aggregates and mean values may describe different distributional shapes.

### 5. Poverty and inequality
The latest HIES poverty rate and Gini coefficient are retained as separate indicators. They are not collapsed into a single official index.

### 6. Formal wage pulse
For the latest available month, median formal-sector wages are compared with the same month a year earlier.

This is kept separate from household income because employee wages and household income measure different concepts.

## Policy triage

A deliberately simple, transparent rule is used for exploratory triage:

- **Higher attention:** poverty is above the state median **and** real median household income growth is below the state median.
- **Watch:** one of those two conditions is met.
- **Relatively resilient:** neither condition is met.

This classification is **not an official policy ranking**. It is a reproducible screening device designed to identify where deeper work may be justified.

## Important caveats

- HIES observations are survey estimates, not administrative counts.
- State CPI represents an average basket; individual households can experience different inflation.
- Formal-sector wages exclude self-employed, gig and other non-formal workers.
- Household income and employee wages are conceptually different and should not be directly substituted for one another.
- The latest administrative wage observations may be revised.
- A state-level screening analysis cannot identify within-state household heterogeneity.
- Correlation is not causation. This project does not estimate the causal effect of inflation on household income or poverty.

## Repository structure

```text
.
├── src/
│   ├── fetch_data.py
│   ├── validate_data.py
│   ├── build_indicators.py
│   └── visualize.py
├── notebooks/
│   └── 01_policy_analysis.ipynb
├── R/
│   └── replicate_real_income_growth.R
├── tests/
│   └── test_indicators.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── reports/
│   └── figures/
├── docs/
│   ├── policy_note.md
│   └── methodology.md
├── .github/workflows/ci.yml
├── streamlit_app.py
├── requirements.txt
└── Makefile
```

## How to run

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

make data
make analyse
make figures
make test
```

Or run the steps individually:

```bash
python src/fetch_data.py
python src/validate_data.py
python src/build_indicators.py
python src/visualize.py
pytest -q
```

Then open:

```bash
jupyter notebook notebooks/01_policy_analysis.ipynb
```


## Interactive Streamlit policy dashboard

The repository also includes an interactive Streamlit interface. It is a **presentation layer on top of the reproducible analytical pipeline**, not a replacement for the scripts, notebook or tests.

The app provides:

- national overview and baseline policy triage;
- state-level household resilience profiles;
- nominal income, CPI and real-income comparisons;
- poverty and inequality exploration;
- formal-wage versus household-income diagnostics;
- an interactive **policy triage sensitivity lab** that makes threshold choices visible;
- methodology, evidence boundaries and official-source documentation;
- CSV download of the analytical table.

Run locally:

```bash
streamlit run streamlit_app.py
```

If `data/processed/state_resilience_metrics.csv` exists, the app uses it. Otherwise, it builds the indicators directly from official DOSM/data.gov.my source files using the same functions in `src/build_indicators.py`.

This design allows the GitHub repository to remain lightweight and makes later deployment to Streamlit Community Cloud straightforward.

## Why Python and R are both included

Python is the primary workflow because it reflects the applicant's strongest professional programming environment. The R script independently replicates the core real-income calculation as a cross-check and demonstrates working familiarity with a second analytical language.

## Reproducibility principle

Every derived metric should be traceable to:
1. an official source;
2. an explicit transformation;
3. a documented caveat;
4. a test where the calculation is material.

## Author

**Farah Ainaa Baharudin**  
Policy Data Science | Decision Intelligence | Data Governance | Evidence-Based Research

This repository is prepared as a public code portfolio. It contains no confidential client or project data.
