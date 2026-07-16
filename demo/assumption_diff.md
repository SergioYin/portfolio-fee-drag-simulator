# Assumption Diff

Version: 0.8.0

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Before: `portfolio_fee_drag_simulator/data/example_assumptions.json`
After: `portfolio_fee_drag_simulator/data/example_assumptions_review.json`
Changed fields: 8

| Field | Before | After | Delta | Direction | Review Impact |
| --- | --- | --- | ---: | --- | --- |
| `cash_return` | `0.02` | `0.018` | `-0.002` | lower | Changes the cash drag spread against the gross return assumption. |
| `realized_gain_rate` | `0.35` | `0.45` | `0.1` | higher | Changes the realized-gain portion of turnover/tax drag arithmetic. |
| `rebalance_cost` | `0.0002` | `0.00035` | `0.00015` | higher | Changes cost per rebalance event used in rebalance drag. |
| `rebalance_frequency` | `annual` | `monthly` | `` | changed | Changes the annual rebalance event count used in rebalance drag. |
| `tax_rate` | `0.15` | `0.2` | `0.05` | higher | Changes turnover/tax drag arithmetic. |
| `taxable_allocation` | `0.7` | `0.85` | `0.15` | higher | Changes the taxable share used in turnover/tax drag arithmetic. |
| `turnover_rate` | `0.12` | `0.65` | `0.53` | higher | Changes turnover/tax drag arithmetic. |
| `years` | `20` | `35` | `15.0` | higher | Changes the compounding horizon and duration over which drag accumulates. |

Field deltas are review prompts only; this output contains no tax, legal, investment, or buy/sell/hold advice.
