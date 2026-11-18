# Methodology

## Research question

Are household incomes across Malaysian states keeping pace with living costs, and where do multiple indicators suggest a need for closer policy attention?

## Unit of analysis

State / Federal Territory.

## Data architecture

The project deliberately combines different statistical products rather than treating them as interchangeable:

- **HIES** provides household income, expenditure, poverty and inequality.
- **CPI** provides a state-level average price index.
- **Formal wage statistics** provide a higher-frequency administrative signal for employees in the formal sector.

The formal wage series is not merged conceptually into household income. It is used only as a separate labour-income pulse.

## Inflation adjustment

For two HIES years, nominal median income growth is adjusted using the ratio of annual-average state CPI indices.

If nominal income rises by 10% and CPI rises by 10%, real growth is zero:

`(1.10 / 1.10) - 1 = 0`

This is preferable to subtracting the two percentages.

## Why no black-box model?

The number of states is small, and the policy problem is primarily one of transparent comparison rather than prediction. A more complex model could create apparent sophistication without improving the decision.

The project therefore uses:
- reproducible transformations;
- descriptive indicators;
- transparent screening rules;
- clear caveats.

That is an intentional methodological choice.

## Triage rule

A state is flagged **higher attention** when:
1. latest poverty is above the state median; and
2. real median household income growth is below the state median.

This rule is not a welfare ranking. It is a way to identify observations that sit on the less favourable side of two interpretable dimensions.

## Revisions

The pipeline downloads source data at run time. Results can change when DOSM revises source datasets. The analysis should therefore always retain:
- run date;
- source URL;
- latest source period;
- version-controlled code.
