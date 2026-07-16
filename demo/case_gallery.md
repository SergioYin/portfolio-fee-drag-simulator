# Portfolio Fee Drag Case Gallery

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Bundled deterministic scenario presets for comparing local fee-drag assumptions.

| Case | Expense Ratio | Cash Allocation | Cash Drag | Turnover/Tax Drag | Rebalance Drag | Total Annual Drag | Total Drag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Cash-Heavy Waitlist | 0.068% | 45.000% | 1.665% | 0.044% | 0.000% | 1.777% | $297,218.06 |
| High-Turnover Taxable Fund | 0.818% | 5.000% | 0.175% | 6.075% | 0.100% | 7.168% | $777,032.57 |
| Low-Cost ETF | 0.045% | 5.000% | 0.150% | 0.066% | 0.010% | 0.272% | $54,874.59 |

## Cases

### Cash-Heavy Waitlist

A staged-deployment scenario with high cash allocation and conservative turnover assumptions.

- Slug: `cash-heavy-waitlist`
- Initial value: $150,000.00
- Annual contribution: $9,000.00
- Years: 25
- Gross return assumption: 5.500%
- Net return after all drags: 3.723%
- Gross future value: $1,032,382.15
- Net future value: $735,164.08

| Ticker | Account | Allocation | Expense Ratio |
| --- | --- | ---: | ---: |
| USMKT | Taxable | 30.000% | 0.030% |
| INTL | Taxable | 15.000% | 0.070% |
| BOND | Retirement | 10.000% | 0.040% |
| CASH | Taxable | 45.000% | 0.100% |

Review notes:
- No ledger warnings.

### High-Turnover Taxable Fund

A taxable fund-style allocation with higher expense, turnover, realized gains, and quarterly rebalancing assumptions.

- Slug: `high-turnover-taxable-fund`
- Initial value: $150,000.00
- Annual contribution: $9,000.00
- Years: 25
- Gross return assumption: 5.500%
- Net return after all drags: -1.667%
- Gross future value: $1,057,702.68
- Net future value: $280,670.11

| Ticker | Account | Allocation | Expense Ratio |
| --- | --- | ---: | ---: |
| ACTIVE | Taxable | 65.000% | 0.850% |
| SMALL | Taxable | 20.000% | 1.100% |
| BOND | Taxable | 10.000% | 0.400% |
| CASH | Taxable | 5.000% | 0.100% |

Review notes:
- No ledger warnings.

### Low-Cost ETF

A diversified low-expense ETF-style allocation with modest turnover and limited cash drag.

- Slug: `low-cost-etf`
- Initial value: $150,000.00
- Annual contribution: $9,000.00
- Years: 25
- Gross return assumption: 5.500%
- Net return after all drags: 5.228%
- Gross future value: $1,057,702.68
- Net future value: $1,002,828.08

| Ticker | Account | Allocation | Expense Ratio |
| --- | --- | ---: | ---: |
| USMKT | Taxable | 50.000% | 0.030% |
| INTL | Taxable | 25.000% | 0.070% |
| BOND | Retirement | 20.000% | 0.040% |
| CASH | Retirement | 5.000% | 0.100% |

Review notes:
- No ledger warnings.
