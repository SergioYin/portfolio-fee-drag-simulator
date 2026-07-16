# Risk Flags

Version: 0.9.0
Status: review

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Holdings: `portfolio_fee_drag_simulator/data/example_holdings.csv`
Assumptions: `portfolio_fee_drag_simulator/data/example_assumptions_review.json`

## Metrics

| Metric | Value |
| --- | ---: |
| `allocation_sum` | `1.0` |
| `cash_allocation` | `0.1` |
| `weighted_expense_ratio` | `0.00047` |
| `max_holding_expense_ratio` | `0.001` |
| `turnover_rate` | `0.65` |
| `turnover_tax_drag_rate` | `0.049725` |
| `years` | `35` |
| `rebalance_frequency` | `monthly` |
| `rebalance_drag_rate` | `0.0042` |

## Review Flags

| Flag | Metric | Value | Threshold | Review Prompt |
| --- | --- | ---: | --- | --- |
| `high_turnover_tax_drag` | `turnover_tax_drag_rate` | `0.049725` | drag >= 0.005 or turnover_rate >= 0.50 | Ask a human reviewer to confirm turnover, realized gain, tax rate, and taxable allocation assumptions before sharing. |
| `long_horizon` | `years` | `35` | >= 30 | Ask a human reviewer to confirm that the horizon is intentional for this static scenario review. |
| `frequent_rebalancing` | `rebalance_frequency` | `monthly` | quarterly or monthly | Ask a human reviewer to confirm rebalance frequency and cost-per-event assumptions. |

Flags are prompts for human review only and are not recommendations, suitability analysis, or tax/legal/investment advice.
